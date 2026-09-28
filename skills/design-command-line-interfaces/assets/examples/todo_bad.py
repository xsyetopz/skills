#!/usr/bin/env python3
"""Baseline: the same task list written without the conventions.

Hand-parses sys.argv, has no -h, prints errors in red to stdout and exits 0,
and asks for a title when run bare, even when stdin is not a terminal.
verify.sh shows check_cli.py rejecting it for each of these.
"""

import sys

tasks: list[str] = []


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        title = input("Title: ")  # waits forever in CI
        tasks.append(title)
        return 0
    if argv[0] == "--help":
        print("todo add TITLE | todo list")
        return 0
    if argv[0] == "add":
        tasks.append(" ".join(argv[1:]))
        print("\x1b[32mOK\x1b[0m")
        return 0
    if argv[0] == "list":
        print("\n".join(tasks))
        return 0
    print(f"\x1b[31mERROR: bad command {argv[0]}\x1b[0m")
    return 0


if __name__ == "__main__":
    main()
