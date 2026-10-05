#!/usr/bin/env python3
"""Recompute p-values from reported test statistics (statcheck-style).

Reads APA-style reports such as "t(28) = 2.20, p = .036",
"F(2, 57) = 3.40, p < .05", "chi2(1) = 4.10, p = .043", "z = 1.96, p = .05",
or "r(48) = .30, p = .034", recomputes the two-tailed p-value (F and chi2
are upper-tail by definition), and flags reports whose stated p cannot
come from the stated statistic after allowing for rounding of the
statistic to its reported decimals. Stdlib only: t and F use the
regularized incomplete beta function, chi2 the regularized gamma
function (Numerical Recipes continued fractions).

This checks internal consistency only. A consistent report can still be
wrong, and an inconsistency may be a typo; read the paper before judging.

Usage: check_stats.py TEXT_FILE [--json]   (or "-" for stdin)
Exit status: 0 all consistent, 1 inconsistencies found, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

REPORT = re.compile(
    r"\b(?P<test>t|F|chi2|χ2|χ²|z|r)\s*"
    r"(?:\(\s*(?P<df1>\d+(?:\.\d+)?)\s*(?:,\s*(?P<df2>\d+(?:\.\d+)?))?\s*\))?"
    r"\s*=\s*(?P<stat>-?\d*\.?\d+)\s*,\s*p\s*(?P<rel>[<>=])\s*(?P<p>0?\.\d+|1)",
)
EPILOG = """\
Exit status:
  0  every report is consistent (or none was found)
  1  at least one report is inconsistent (flagged)
  2  bad usage, or TEXT_FILE is unreadable or not UTF-8

Output: one "ok" or "FLAG" line per report with the computed p and its
range, then "N report(s), N inconsistent". --json prints {"reports":
[{report, test, consistent, computed_p, low, high, detail}], "count": N,
"inconsistent": N}; computed_p, low, and high are null when degrees of
freedom are missing.

Examples:
  python3 scripts/check_stats.py results.txt
  pdftotext paper.pdf - | python3 scripts/check_stats.py -
  python3 scripts/check_stats.py results.txt --json \\
    | jq '.reports[] | select(.consistent | not)'
"""


def _betacf(a: float, b: float, x: float) -> float:
    tiny, eps = 1e-300, 3e-14
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c if abs(1 + aa / c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c if abs(1 + aa / c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < eps:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1 - x)
    )
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def gammainc_upper(s: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(s, x)."""
    if x <= 0:
        return 1.0
    if x < s + 1:  # series for P, then Q = 1 - P
        term = total = 1 / s
        n = s
        for _ in range(1000):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 3e-14:
                break
        return 1 - total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    tiny = 1e-300
    b = x + 1 - s
    c, d = 1 / tiny, 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - s)
        b += 2
        d = an * d + b
        d = 1 / (d if abs(d) > tiny else tiny)
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 3e-14:
            break
    return math.exp(-x + s * math.log(x) - math.lgamma(s)) * h


def p_value(test: str, stat: float, df1: float | None, df2: float | None) -> float:
    if test == "z":
        return math.erfc(abs(stat) / math.sqrt(2))
    if df1 is None:
        raise ValueError(f"{test} needs degrees of freedom")
    if test == "t":
        return betainc(df1 / 2, 0.5, df1 / (df1 + stat * stat))
    if test == "r":  # t = r * sqrt(df / (1 - r^2)), df = n - 2
        if abs(stat) >= 1:
            return 0.0  # a perfect correlation: t is infinite
        t = stat * math.sqrt(df1 / (1 - stat * stat))
        return betainc(df1 / 2, 0.5, df1 / (df1 + t * t))
    if test == "F":
        if df2 is None:
            raise ValueError("F needs two degrees of freedom")
        return betainc(df2 / 2, df1 / 2, df2 / (df2 + df1 * stat))
    return gammainc_upper(df1 / 2, stat / 2)  # chi2


def decimals(text: str) -> int:
    return len(text.split(".")[1]) if "." in text else 0


def check_report(match: re.Match) -> tuple[bool, str]:
    result = assess(match)
    return result["consistent"], result["detail"]


def assess(match: re.Match) -> dict:
    """The check of one report, with the computed p-value and its range."""
    test = {"χ2": "chi2", "χ²": "chi2"}.get(match["test"], match["test"]) or ""
    result = {
        "report": match.group(0),
        "test": test,
        "consistent": False,
        "computed_p": None,
        "low": None,
        "high": None,
        "detail": "missing degrees of freedom",
    }
    df1 = float(match["df1"]) if match["df1"] else None
    df2 = float(match["df2"]) if match["df2"] else None
    if (test in {"t", "r", "chi2"} and df1 is None) or (test == "F" and df2 is None):
        return result
    stat = float(match["stat"])
    if test == "r" and abs(stat) > 1:
        result["detail"] = "r outside -1..1; not a correlation"
        return result
    half = 0.5 * 10 ** -decimals(match["stat"])  # rounding of the statistic
    lows_highs = [
        p_value(test, s, df1, df2) for s in (abs(stat) - half, abs(stat) + half)
    ]
    low, high = min(lows_highs), max(lows_highs)
    computed = p_value(test, abs(stat), df1, df2)
    reported = float(match["p"])
    rel = match["rel"]
    p_half = 0.5 * 10 ** -decimals(match["p"])
    if rel == "=":
        ok = low - p_half <= reported <= high + p_half
    elif rel == "<":
        ok = low < reported
    else:
        ok = high > reported
    result.update(
        consistent=ok,
        computed_p=computed,
        low=low,
        high=high,
        detail=f"computed p = {computed:.4f} (range {low:.4f}-{high:.4f})",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        usage="check_stats.py [-h] [--json] TEXT_FILE|-",
        description=(__doc__ or "").strip(),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file", metavar="TEXT_FILE", help='text to scan; "-" reads stdin'
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        text = (
            sys.stdin.read() if args.file == "-" else Path(args.file).read_text("utf-8")
        )
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {args.file}: {error}; expected a UTF-8 text file "
            '(convert PDFs first, e.g. pdftotext paper.pdf -), or "-" for stdin',
            file=sys.stderr,
        )
        return 2
    results = [assess(match) for match in REPORT.finditer(text)]
    bad = sum(not result["consistent"] for result in results)
    if args.json:
        report = {"reports": results, "count": len(results), "inconsistent": bad}
        print(json.dumps(report, indent=2))
        return 1 if bad else 0
    for result in results:
        mark = "ok  " if result["consistent"] else "FLAG"
        print(f"{mark} {result['report']!r}: {result['detail']}")
    print(f"{len(results)} report(s), {bad} inconsistent")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
