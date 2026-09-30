#!/usr/bin/env python3
"""Check matching-decompilation evidence records and fail closed.

Reads `acceptance.json` (the current acceptance claim) and, optionally,
`iterations.json` (the attempt log). Schemas are described in
references/evidence-records.md of the build-matching-decompilations skill.

Acceptance checks:
  - every recorded SHA-256 (reference binary, toolchain files, sources,
    build output, symbol manifest) is recomputed from the file on disk;
    a missing file or a different hash is a defect
  - the reference binary is not tracked by Git
  - the comparison covers full functions or the full image, masks
    nothing, and leaves no relocation unresolved
  - coverage counts only functions with origin "reconstructed" and status
    "matched"; the claimed numbers must equal the recomputed ones
  - at least one negative control exists and each one failed the verifier
  - at least one ABI boundary check exists and each one passed

Iteration checks: unique increasing ids, 64-digit hex hashes, a known
result, and differing byte counts consistent with the result. With both
files, each function accepted as matched must have a latest attempt whose
result is "match".

Usage: check_match_evidence.py [--acceptance FILE] [--iterations FILE]
                               [--root DIR] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from acceptance_checks import SHA256, Report, check_acceptance

EPILOG = """\
Exit status:
  0  no defects
  1  at least one defect (printed as "DEFECT ...")
  2  bad usage, or a file that is unreadable or not a JSON object

Paths inside acceptance.json resolve from --root (default: the directory
that contains acceptance.json).

Examples:
  python3 scripts/check_match_evidence.py --acceptance evidence/acceptance.json
  python3 scripts/check_match_evidence.py --iterations evidence/iterations.json
  python3 scripts/check_match_evidence.py --acceptance evidence/acceptance.json \\
      --iterations evidence/iterations.json --root . --json
"""

RESULTS = {"match", "nonmatching", "build-failed"}


class InputError(Exception):
    """An input file cannot be read as a JSON object."""


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read {path}: {error}") from error
    if not isinstance(data, dict):
        raise InputError(f"{path}: top level must be a JSON object")
    return data


def check_iterations(data: dict[str, Any], report: Report) -> dict[str, str]:
    """Check the attempt log; return each function's latest result."""
    defects = report.defects
    if data.get("schema_version") != 1:
        defects.append("iterations: schema_version must be 1")
    attempts = data.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        defects.append("iterations: attempts must be a non-empty list")
        return {}
    report.attempts = len(attempts)
    latest: dict[str, str] = {}
    previous = 0
    for index, attempt in enumerate(attempts):
        label = f"attempts[{index}]"
        if not isinstance(attempt, dict):
            defects.append(f"{label}: expected an object")
            continue
        number = attempt.get("id")
        if (
            not isinstance(number, int)
            or isinstance(number, bool)
            or number <= previous
        ):
            defects.append(f"{label}: id must be an integer greater than {previous}")
        else:
            previous = number
        for key in ("function", "change", "diff_summary"):
            if not isinstance(attempt.get(key), str) or not attempt[key].strip():
                defects.append(f"{label}: missing {key}")
        for key in ("source_sha256", "toolchain_sha256"):
            value = attempt.get(key)
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                defects.append(f"{label}: {key} must be 64 lowercase hex digits")
        result, differing = attempt.get("result"), attempt.get("differing_bytes")
        if result not in RESULTS:
            defects.append(
                f"{label}: result {result!r} is not one of {sorted(RESULTS)}"
            )
        elif result == "match" and differing != 0:
            defects.append(f"{label}: result 'match' needs differing_bytes 0")
        elif result == "nonmatching" and (
            not isinstance(differing, int)
            or isinstance(differing, bool)
            or differing <= 0
        ):
            defects.append(f"{label}: result 'nonmatching' needs differing_bytes > 0")
        elif result == "build-failed" and differing is not None:
            defects.append(f"{label}: result 'build-failed' needs differing_bytes null")
        if isinstance(attempt.get("function"), str) and result in RESULTS:
            latest[attempt["function"]] = str(result)
    return latest


def check(
    acceptance: dict[str, Any] | None,
    iterations: dict[str, Any] | None,
    root: Path,
) -> Report:
    report = Report()
    statuses = (
        check_acceptance(acceptance, root, report) if acceptance is not None else {}
    )
    latest = check_iterations(iterations, report) if iterations is not None else {}
    if acceptance is not None and iterations is not None:
        for symbol, status in statuses.items():
            if status != "matched":
                continue
            if symbol not in latest:
                report.defects.append(
                    f"function {symbol}: accepted as matched with no attempt "
                    "in iterations.json"
                )
            elif latest[symbol] != "match":
                report.defects.append(
                    f"function {symbol}: accepted as matched, but its latest "
                    f"attempt is {latest[symbol]!r}"
                )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--acceptance", type=Path, help="acceptance.json to check")
    parser.add_argument("--iterations", type=Path, help="iterations.json to check")
    parser.add_argument(
        "--root",
        type=Path,
        help="directory that acceptance paths resolve from "
        "(default: the directory of --acceptance)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    if args.acceptance is None and args.iterations is None:
        parser.print_usage(sys.stderr)
        print(
            "error: give --acceptance FILE, --iterations FILE, or both",
            file=sys.stderr,
        )
        return 2
    try:
        acceptance = load(args.acceptance) if args.acceptance else None
        iterations = load(args.iterations) if args.iterations else None
    except InputError as error:
        print(f"error: {error}; expected a JSON object", file=sys.stderr)
        return 2
    root = args.root or (args.acceptance.parent if args.acceptance else Path("."))
    if not root.is_dir():
        print(f"error: --root {root} is not a directory", file=sys.stderr)
        return 2
    report = check(acceptance, iterations, root)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        summary = [f"defects={len(report.defects)}"]
        if report.total_bytes is not None:
            summary.append(
                f"matched_bytes={report.matched_bytes} total_bytes={report.total_bytes}"
            )
        if report.attempts is not None:
            summary.append(f"attempts={report.attempts}")
        print(" ".join(summary))
        for defect in report.defects:
            print(f"  DEFECT {defect}")
    return 1 if report.defects else 0


if __name__ == "__main__":
    raise SystemExit(main())
