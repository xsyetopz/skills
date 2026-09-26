#!/usr/bin/env python3
"""Print the most frequent words in text files or stdin."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter


def top_words(text: str, count: int) -> list[tuple[str, int]]:
    words = re.findall(r"[a-z']+", text.lower())
    return Counter(words).most_common(count)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wordfreq", description=__doc__)
    parser.add_argument("files", nargs="*", help="files to read (default: stdin)")
    parser.add_argument("-n", "--top", type=int, default=3, help="words to show")
    args = parser.parse_args(argv)
    parts = []
    for name in args.files:
        with open(name, encoding="utf-8") as handle:
            parts.append(handle.read())
    text = "".join(parts) if args.files else sys.stdin.read()
    for word, number in top_words(text, args.top):
        print(f"{number} {word}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
