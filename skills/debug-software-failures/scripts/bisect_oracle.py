#!/usr/bin/env python3
"""Map a test command's explicit outcomes to git bisect run exit codes.

Does not alter Git state. Runs argv directly (no shell). 0 = good, 1 = known
regression, 125 = explicitly classified untestable revision, 128 = abort.
Unknown exits, missing commands, signals, and timeouts abort instead of becoming
false bad revisions. Only use after testing both good and bad endpoints.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

EPILOG = """\
Exit status (the git bisect run contract):
  0    the command exited 0: good revision
  1    the command exited with a --bad-exit status: bad revision
  125  the command exited with a --skip-exit status: untestable, skip it
  128  anything else (unknown status, signal, timeout, missing command,
       bad --cwd): git bisect run stops instead of marking a revision
  2    usage error in this script's own options; git bisect run would
       read 2 as bad, so run the command once by hand before bisecting

Output: the command's own stdout and stderr pass through unchanged; this
script adds only a "bisect oracle abort: ..." line on stderr for 128.

Examples:
  python3 scripts/bisect_oracle.py --bad-exit 1 --skip-exit 3 -- \\
      python3 -m pytest tests/test_invoice.py
  git bisect run python3 scripts/bisect_oracle.py --timeout 300 -- make check
"""


def classify(code: int, bad: set[int], skip: set[int]) -> int:
    if code == 0:
        return 0
    if code in bad:
        return 1
    if code in skip:
        return 125
    return 128


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bad-exit", type=int, action="append", help="known defect status; default: 1"
    )
    parser.add_argument(
        "--skip-exit",
        type=int,
        action="append",
        default=[],
        help="known untestable status; none by default",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        help="seconds; a timeout aborts, never marks a revision bad",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        help="command directory; normally inherit bisect worktree cwd",
    )
    parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="-- executable arg ..."
    )
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a test command after --")
    bad, skip = set(args.bad_exit or [1]), set(args.skip_exit)
    if bad & skip or any(code < 1 or code > 125 for code in bad | skip):
        parser.error(
            "bad/skip statuses must be disjoint and in 1..125; shell errors and signals must abort"
        )
    if args.timeout is not None and (
        not math.isfinite(args.timeout) or args.timeout <= 0
    ):
        parser.error("--timeout must be finite and positive")
    try:
        result = subprocess.run(
            command, cwd=args.cwd, timeout=args.timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        detail = f": {exc}" if str(exc) else ""
        print(f"bisect oracle abort: {type(exc).__name__}{detail}", file=sys.stderr)
        return 128
    status = classify(result.returncode, bad, skip)
    if status == 128:
        print(
            f"bisect oracle abort: unclassified command exit {result.returncode}",
            file=sys.stderr,
        )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
