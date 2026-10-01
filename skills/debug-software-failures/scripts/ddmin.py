#!/usr/bin/env python3
"""Minimize a failing input file with delta debugging (ddmin).

Implements the ddmin algorithm of Zeller and Hildebrandt, "Simplifying and
Isolating Failure-Inducing Input" (IEEE TSE 28(2), 2002): split the input
into n chunks, keep any chunk or complement that still fails, otherwise
double n, until the result is 1-minimal (removing any single unit makes the
failure disappear).

The oracle is a command given after `--` as separate arguments (no shell, so
Windows backslashes survive). For each candidate, the candidate is written to
a temporary file and the command runs with `{}` replaced by that path. The
candidate "fails" when the command's exit status equals --fail-status
(default 1) and, if given, its stdout+stderr contains --fail-text. Any other
outcome counts as "passes or is unresolved", so a crash of a different kind
is never mistaken for the original failure.

Usage:
  ddmin.py INPUT [--fail-status 1] [--fail-text 'ValueError']
           [--unit line|char] [--output FILE] -- python3 parser.py {}

Prints the reduced input (or writes --output) and a summary line to stderr:
  units N -> M, oracle runs K
Exit status: 0 reduced, 1 the original input does not fail, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Sequence

EPILOG = """\
Exit status:
  0  reduced (the result still fails the oracle)
  1  the original input does not fail the oracle; nothing was reduced
  2  bad input: unreadable INPUT, no oracle command after --, an oracle
     without {}, an oracle command that cannot be started, or an unwritable
     --output

Output: the reduced input on stdout (or in --output FILE), and the line
"units N -> M, oracle runs K" on stderr. --json prints one object instead:
{"reduced": TEXT, "units_before": N, "units_after": M, "oracle_runs": K,
"output": FILE or null}; on exit 1 and 2 stdout stays empty.

Examples:
  python3 scripts/ddmin.py big.csv --fail-text 'expected 3 fields' \\
      --output min.csv -- python3 parser.py {}
  python3 scripts/ddmin.py crash.txt --fail-status 139 --unit char --json \\
      -- ./app {}
"""


def make_oracle(
    command: Sequence[str], fail_status: int, fail_text: str | None, unit: str
) -> tuple[Callable[[Sequence[str]], bool], list[int]]:
    runs = [0]

    def fails(units: Sequence[str]) -> bool:
        runs[0] += 1
        text = "".join(units)  # line units keep their newlines
        with tempfile.NamedTemporaryFile(
            "w", suffix=".input", delete=False, encoding="utf-8", newline=""
        ) as handle:
            handle.write(text)
            path = handle.name
        try:
            argv = [path if part == "{}" else part for part in command]
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return False
        finally:
            Path(path).unlink(missing_ok=True)
        if result.returncode != fail_status:
            return False
        return fail_text is None or fail_text in (result.stdout + result.stderr)

    return fails, runs


def ddmin(units: list[str], fails: Callable[[list[str]], bool]) -> list[str]:
    n = 2
    while len(units) >= 2:
        chunk = len(units) // n
        subsets = [units[i : i + chunk] for i in range(0, len(units), chunk)]
        reduced = False
        for index, subset in enumerate(subsets):
            complement = [u for j, s in enumerate(subsets) if j != index for u in s]
            if fails(subset):
                units, n, reduced = subset, 2, True
                break
            if fails(complement):
                units, n, reduced = complement, max(n - 1, 2), True
                break
        if not reduced:
            if n >= len(units):
                break
            n = min(len(units), n * 2)
    return units


def split_units(text: str, unit: str) -> list[str]:
    return list(text) if unit == "char" else text.splitlines(keepends=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="failing input file (UTF-8)")
    parser.usage = "ddmin.py [options] INPUT -- ORACLE_PROGRAM [ARG ...] {}"
    parser.add_argument(
        "--fail-status", type=int, default=1, help="failing exit status (default 1)"
    )
    parser.add_argument("--fail-text", help="text the failing output must contain")
    parser.add_argument(
        "--unit", choices=("line", "char"), default="line", help="default: line"
    )
    parser.add_argument("--output", help="write the reduced input to this file")
    parser.add_argument(
        "--json", action="store_true", help="print one JSON result on stdout"
    )
    arguments = sys.argv[1:] if argv is None else argv
    if "--" in arguments:
        split = arguments.index("--")
        arguments, oracle_words = arguments[:split], arguments[split + 1 :]
    else:
        oracle_words = []
    args = parser.parse_args(arguments)
    try:
        with open(args.input, encoding="utf-8", newline="") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {args.input}: {error}; "
            "pass an existing UTF-8 failing input file",
            file=sys.stderr,
        )
        return 2
    if not oracle_words:
        print(
            "error: give the oracle command after --, e.g. -- python3 check.py {}",
            file=sys.stderr,
        )
        return 2
    if "{}" not in oracle_words:
        print("error: the oracle must contain {} for the input path", file=sys.stderr)
        return 2
    fails, runs = make_oracle(oracle_words, args.fail_status, args.fail_text, args.unit)
    units = split_units(text, args.unit)
    try:
        if not fails(units):
            print("error: the original input does not fail the oracle", file=sys.stderr)
            return 1
        reduced = ddmin(units, fails)
    except OSError as error:
        print(
            f"error: cannot run the oracle '{oracle_words[0]}': "
            f"{error.strerror or error}; check the command and its path",
            file=sys.stderr,
        )
        return 2
    result = "".join(reduced)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="") as handle:
                handle.write(result)
        except OSError as error:
            print(f"error: cannot write --output: {error}", file=sys.stderr)
            return 2
    if args.json:
        report = {
            "reduced": result,
            "units_before": len(units),
            "units_after": len(reduced),
            "oracle_runs": runs[0],
            "output": args.output,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif not args.output:
        sys.stdout.write(result)
    print(
        f"units {len(units)} -> {len(reduced)}, oracle runs {runs[0]}", file=sys.stderr
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
