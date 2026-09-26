#!/usr/bin/env python3
"""Run each (variant, test target) pair and compare failing tests.

Every case in expectations.json names a VARIANT (empty for the reference
implementation), a unittest target, and the exact set of test methods that
must fail. A case passes only when the observed set equals that set, so a
test that fails for the wrong variant, or passes a mutant it should kill,
is reported.

Usage: run_matrix.py [--only SUBSTRING]
Exit status: 0 all cases match, 1 a mismatch, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAILURE = re.compile(r"^(?:FAIL|ERROR): (\w+) \(", re.MULTILINE)


def failing_tests(variant: str, target: str) -> set[str]:
    env = {**os.environ, "VARIANT": variant, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "unittest", target],
        cwd=HERE,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    failed = set(FAILURE.findall(result.stderr))
    if result.returncode != 0 and not failed:
        failed.add(f"<runner exit {result.returncode}>")
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--only", default="")
    args = parser.parse_args(argv)
    try:
        cases = json.loads((HERE / "expectations.json").read_text())["cases"]
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    mismatches = 0
    checked = 0
    for case in cases:
        label = f"{case['variant'] or 'reference'} :: {case['target']}"
        if args.only not in label:
            continue
        checked += 1
        expected = set(case["failing"])
        observed = failing_tests(case["variant"], case["target"])
        if observed == expected:
            verdict = "fails " + ",".join(sorted(expected)) if expected else "passes"
            print(f"ok   {label}: {verdict}")
        else:
            mismatches += 1
            print(
                f"MISMATCH {label}: expected {sorted(expected)} "
                f"observed {sorted(observed)}"
            )
    print(f"{checked - mismatches}/{checked} cases match")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
