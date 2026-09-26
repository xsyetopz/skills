"""Print the last lines of a log file, optionally only one level."""

import argparse
import sys
from collections import deque


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logtail", description=__doc__)
    parser.add_argument("file")
    parser.add_argument("-n", "--lines", type=int, default=10, help="lines to show")
    parser.add_argument("--level", help="only lines containing [LEVEL]")
    args = parser.parse_args(argv)
    with open(args.file, encoding="utf-8") as handle:
        lines = (l.rstrip("\n") for l in handle)
        if args.level:
            lines = (l for l in lines if f"[{args.level.upper()}]" in l)
        for line in deque(lines, maxlen=args.lines):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
