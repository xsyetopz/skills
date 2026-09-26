#!/usr/bin/env python3
"""Summarize and compare JMH JSON results (``-rf json``) without guessing.

One file: print every row and check named baseline:candidate pairs.
Two files: match rows by benchmark, mode, threads, and params and report
candidate/baseline ratios. Exit 0: all checks pass; 1: a check failed;
2: invalid or incomparable input. Files are never modified.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOC = "gc.alloc.rate.norm"
EPILOG = """\
Exit status:
  0  every --alloc-* check passes and, with two files, no row regressed
     beyond --fail-regression
  1  a check failed or a row regressed
  2  invalid or incomparable input (unreadable JSON, duplicate or missing
     rows, unit mismatch, ambiguous benchmark name, missing gc profiler data)

Output: one file prints a table of rows and one PASS/FAIL line per check;
two files print one ratio line per row and FAIL lines for regressions.
--json prints {"rows": [...], "checks": [...]} for one file or
{"comparisons": [...]} for two; NaN values become null.

Examples:
  python3 scripts/jmh_compare.py results.json --alloc-lower parseOld:parseNew
  python3 scripts/jmh_compare.py before.json after.json --fail-regression 5
  python3 scripts/jmh_compare.py before.json after.json --json
"""


def number_or_none(value: float | None) -> float | None:
    """JSON has no NaN; report an unknown value as null."""
    return None if value is None or math.isnan(value) else value


class InputError(ValueError):
    """The input cannot support the requested comparison."""


@dataclass(frozen=True)
class Row:
    name: str
    mode: str
    threads: int
    params: tuple[tuple[str, str], ...]
    score: float
    error: float
    unit: str
    alloc: float | None

    @property
    def identity(self) -> tuple[str, str, int, tuple[tuple[str, str], ...]]:
        return (self.name, self.mode, self.threads, self.params)

    @property
    def label(self) -> str:
        short = self.name.rsplit(".", 2)
        text = ".".join(short[-2:])
        if self.params:
            text += "[" + ",".join(f"{k}={v}" for k, v in self.params) + "]"
        return text


def _number(value: object, where: str) -> float:
    if value == "NaN":
        return math.nan
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{where}: expected a number, got {value!r}")
    return float(value)


def _secondary(metrics: dict[str, object], key: str) -> object | None:
    """Match by suffix: older JMH versions prefix secondary keys (a marker)."""
    for name, value in metrics.items():
        if name.endswith(key):
            return value
    return None


def load(path: Path) -> list[Row]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"{path}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise InputError(f"{path}: expected a non-empty JMH JSON array")
    rows = []
    for i, item in enumerate(data):
        where = f"{path}[{i}]"
        try:
            primary = item["primaryMetric"]
            params = item.get("params") or {}
            secondary = item.get("secondaryMetrics") or {}
            alloc_metric = _secondary(secondary, ALLOC)
            alloc = None
            if isinstance(alloc_metric, dict):
                alloc = _number(alloc_metric["score"], where + " alloc")
            rows.append(
                Row(
                    name=str(item["benchmark"]),
                    mode=str(item["mode"]),
                    threads=int(item["threads"]),
                    params=tuple(sorted((str(k), str(v)) for k, v in params.items())),
                    score=_number(primary["score"], where + " score"),
                    error=_number(primary["scoreError"], where + " error"),
                    unit=str(primary["scoreUnit"]),
                    alloc=alloc,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, InputError):
                raise
            raise InputError(f"{where}: malformed JMH row ({exc})") from exc
    seen: set[tuple[str, str, int, tuple[tuple[str, str], ...]]] = set()
    for row in rows:
        if row.identity in seen:
            raise InputError(f"{path}: duplicate row {row.label} {row.mode}")
        seen.add(row.identity)
    return rows


def lower_is_better(mode: str) -> bool:
    if mode in ("avgt", "sample", "ss"):
        return True
    if mode == "thrpt":
        return False
    raise InputError(f"unsupported JMH mode {mode!r}")


def overlaps(a: Row, b: Row) -> bool:
    """True when the two 99.9% intervals overlap (or an error is unknown)."""
    if math.isnan(a.error) or math.isnan(b.error):
        return True
    return abs(a.score - b.score) <= a.error + b.error


def fmt(value: float | None) -> str:
    if value is None:
        return "-"
    if math.isnan(value):
        return "NaN"
    return f"{value:,.3f}"


def print_rows(rows: list[Row]) -> None:
    print(f"{'benchmark':48} {'mode':5} {'score':>14} {'error':>12} unit  alloc B/op")
    for r in rows:
        print(
            f"{r.label:48} {r.mode:5} {fmt(r.score):>14} {fmt(r.error):>12} "
            f"{r.unit}  {fmt(r.alloc)}"
        )


def find(rows: list[Row], short: str) -> Row:
    matches = [r for r in rows if r.name == short or r.name.endswith("." + short)]
    if len(matches) != 1:
        raise InputError(f"{short!r} matches {len(matches)} rows; use a longer name")
    return matches[0]


def row_record(r: Row) -> dict:
    return {
        "benchmark": r.name,
        "label": r.label,
        "mode": r.mode,
        "threads": r.threads,
        "params": dict(r.params),
        "score": number_or_none(r.score),
        "error": number_or_none(r.error),
        "unit": r.unit,
        "alloc": number_or_none(r.alloc),
    }


def check_pair(
    rows: list[Row],
    spec: str,
    kind: str,
    margin: float,
    records: list[dict] | None = None,
) -> bool:
    if spec.count(":") != 1:
        raise InputError(f"pair {spec!r} must be BASELINE:CANDIDATE")
    base_name, cand_name = spec.split(":")
    base, cand = find(rows, base_name), find(rows, cand_name)
    if base.alloc is None or cand.alloc is None:
        raise InputError(f"{spec}: {ALLOC} missing; run JMH with -prof gc")
    if kind == "lower":
        ok = cand.alloc < base.alloc * (1 - margin)
        claim = f"candidate < baseline x {1 - margin:g}"
    else:
        ok = abs(cand.alloc - base.alloc) <= max(1.0, base.alloc * margin)
        claim = f"|delta| <= max(1 B, {margin:g} x baseline)"
    status = "PASS" if ok else "FAIL"
    if records is not None:
        records.append(
            {
                "check": f"alloc-{kind}",
                "baseline": base.label,
                "candidate": cand.label,
                "baseline_alloc": number_or_none(base.alloc),
                "candidate_alloc": number_or_none(cand.alloc),
                "claim": claim,
                "ok": ok,
            }
        )
        return ok
    print(
        f"{status} alloc {base.label} {fmt(base.alloc)} B/op -> "
        f"{cand.label} {fmt(cand.alloc)} B/op ({claim})"
    )
    return ok


def compare_files(
    base: list[Row],
    cand: list[Row],
    fail_pct: float | None,
    records: list[dict] | None = None,
) -> bool:
    by_id = {r.identity: r for r in cand}
    missing = [r.label for r in base if r.identity not in by_id]
    extra = {r.identity for r in cand} - {r.identity for r in base}
    if missing or extra:
        raise InputError(f"row sets differ: missing={missing} extra={len(extra)}")
    ok = True
    for b in base:
        c = by_id[b.identity]
        if b.unit != c.unit:
            raise InputError(f"{b.label}: unit {b.unit} vs {c.unit}")
        ratio = c.score / b.score if b.score else math.inf
        worse = ratio > 1 if lower_is_better(b.mode) else ratio < 1
        change = abs(ratio - 1) * 100
        noise = overlaps(b, c)
        verdict = "within error" if noise else ("worse" if worse else "better")
        regressed = fail_pct is not None and worse and not noise and change > fail_pct
        if records is not None:
            records.append(
                {
                    "label": b.label,
                    "mode": b.mode,
                    "unit": b.unit,
                    "baseline": number_or_none(b.score),
                    "candidate": number_or_none(c.score),
                    "ratio": None if math.isinf(ratio) else number_or_none(ratio),
                    "verdict": verdict,
                    "baseline_alloc": number_or_none(b.alloc),
                    "candidate_alloc": number_or_none(c.alloc),
                    "regression": regressed,
                }
            )
            ok = ok and not regressed
            continue
        print(
            f"{b.label:48} {fmt(b.score)} -> {fmt(c.score)} {b.unit} "
            f"ratio {ratio:.3f} ({verdict}) alloc {fmt(b.alloc)} -> {fmt(c.alloc)}"
        )
        if fail_pct is not None and worse and not noise and change > fail_pct:
            print(f"FAIL regression {b.label}: {change:.1f}% > {fail_pct:g}%")
            ok = False
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize and compare JMH JSON results.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("results", nargs="+", type=Path, help="1 or 2 JMH JSON files")
    parser.add_argument(
        "--alloc-lower",
        action="append",
        default=[],
        metavar="BASE:CAND",
        help=f"assert CAND {ALLOC} is below BASE by more than --margin",
    )
    parser.add_argument(
        "--alloc-same",
        action="append",
        default=[],
        metavar="BASE:CAND",
        help=f"assert {ALLOC} differs by at most max(1 B, margin x BASE)",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.1,
        help="relative allocation margin in [0, 1) (default: 0.1)",
    )
    parser.add_argument(
        "--fail-regression",
        type=float,
        metavar="PCT",
        help="two-file mode: exit 1 when a row is worse beyond error and PCT",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        if len(args.results) > 2:
            raise InputError("pass one or two result files")
        if not 0 <= args.margin < 1:
            raise InputError("--margin must be in [0, 1)")
        first = load(args.results[0])
        if args.json:
            return report_json(first, args)
        if len(args.results) == 2:
            return (
                0
                if compare_files(first, load(args.results[1]), args.fail_regression)
                else 1
            )
        print_rows(first)
        ok = True
        for spec in args.alloc_lower:
            ok &= check_pair(first, spec, "lower", args.margin)
        for spec in args.alloc_same:
            ok &= check_pair(first, spec, "same", args.margin)
        return 0 if ok else 1
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def report_json(first: list[Row], args: argparse.Namespace) -> int:
    """The --json form of main(); raises InputError like main()'s checks."""
    records: list[dict] = []
    if len(args.results) == 2:
        second = load(args.results[1])
        ok = compare_files(first, second, args.fail_regression, records)
        print(json.dumps({"comparisons": records}, indent=2))
        return 0 if ok else 1
    ok = True
    for spec in args.alloc_lower:
        ok &= check_pair(first, spec, "lower", args.margin, records)
    for spec in args.alloc_same:
        ok &= check_pair(first, spec, "same", args.margin, records)
    report = {"rows": [row_record(r) for r in first], "checks": records}
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
