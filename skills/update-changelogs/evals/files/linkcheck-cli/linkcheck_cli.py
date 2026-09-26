"""Report Markdown links whose relative target file does not exist."""

import pathlib
import re
import sys


def main() -> int:
    missing = 0
    for path in map(pathlib.Path, sys.argv[1:]):
        for target in re.findall(r"\]\(([^)#:]+)\)", path.read_text(encoding="utf-8")):
            if not (path.parent / target).exists():
                print(f"{path}: missing {target}")
                missing += 1
    return 1 if missing else 0
