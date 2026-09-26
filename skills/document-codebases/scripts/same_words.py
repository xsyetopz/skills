#!/usr/bin/env python3
"""Check that a formatting-only Markdown edit kept every word.

Compares the word sequences of two versions after removing Markdown
syntax that carries no words: heading and list markers, emphasis marks,
backticks, table pipes, blockquote markers, and line wrapping. Link
URLs are kept as words, so a changed URL is reported. Code blocks are
compared line by line, because whitespace can matter inside them.

Usage: same_words.py BEFORE.md AFTER.md [--json]
Exit status: 0 same words and code, 1 differences (printed), 2 bad input.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(```+|~~~+)")
MARKERS = re.compile(r"^\s*(#{1,6}\s|>\s?|[-*+]\s|\d+[.)]\s|\|)")
SYMBOLS = re.compile(r"[*_`|]")
EPILOG = """\
Exit status:
  0  same words and code
  1  differences (printed)
  2  bad input: wrong number of arguments or an unreadable file

Output: one "words replace|delete|insert: -[...] +[...]" line per word
change, a unified diff of changed code-block lines, then "same words and
code" or "N difference(s)". --json prints {"same": bool, "differences":
N, "words": [{change, removed, added}], "code_diff": [lines]}.

Examples:
  git show HEAD:README.md > /tmp/before.md
  python3 scripts/same_words.py /tmp/before.md README.md
  python3 scripts/same_words.py before.md after.md --json | jq '.words'
"""


def split(text: str) -> tuple[list[str], list[str]]:
    """Return (prose words, code lines)."""
    words: list[str] = []
    code: list[str] = []
    in_code = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_code = not in_code
            code.append(line.strip())
            continue
        if in_code:
            code.append(line.rstrip())
            continue
        while MARKERS.match(line):
            line = MARKERS.sub("", line, count=1)
        line = re.sub(r"\]\(([^)]*)\)", r" \1 ", line)  # keep link targets
        line = re.sub(r"^\s*\|?\s*:?-{3,}.*$", "", line)  # table rule rows
        words += SYMBOLS.sub(" ", line.replace("[", " ").replace("]", " ")).split()
    return words, code


def compare(before: str, after: str) -> tuple[list[dict], list[str]]:
    """Word changes ({change, removed, added}) and code-block diff lines."""
    (words_a, code_a), (words_b, code_b) = split(before), split(after)
    words = [
        {
            "change": tag,
            "removed": " ".join(words_a[i1:i2]),
            "added": " ".join(words_b[j1:j2]),
        }
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            a=words_a, b=words_b, autojunk=False
        ).get_opcodes()
        if tag != "equal"
    ]
    code = list(
        difflib.unified_diff(code_a, code_b, "before code", "after code", lineterm="")
    )
    return words, code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("before", help="Markdown file before the edit")
    parser.add_argument("after", help="Markdown file after the edit")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        before, after = (
            Path(a).read_text(encoding="utf-8") for a in (args.before, args.after)
        )
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: {error}; expected two readable UTF-8 Markdown files",
            file=sys.stderr,
        )
        return 2
    words, code = compare(before, after)
    problems = len(words) + len(code)
    if args.json:
        report = {
            "same": problems == 0,
            "differences": problems,
            "words": words,
            "code_diff": code,
        }
        print(json.dumps(report, indent=2))
        return 1 if problems else 0
    for word in words:
        print(f"words {word['change']}: -[{word['removed']}] +[{word['added']}]")
    for line in code:
        print(line)
    print("same words and code" if problems == 0 else f"{problems} difference(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
