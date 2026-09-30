#!/usr/bin/env python3
"""Write or check the linked "## Contents" list of Markdown files.

The list under an existing "## Contents" heading is rebuilt from the
file's headings of levels 2 to --max-level (the Contents heading itself
excluded), one "- [Heading](#anchor)" line per heading, nested two spaces
per level. Anchors follow GitHub's rules: lower-case, markup removed,
punctuation removed, spaces to hyphens, "-1", "-2" appended to repeats.
Headings inside fenced code blocks are ignored.

An entry longer than --width becomes a reference link "[Heading][toc-N]"
with its "[toc-N]: #anchor" definition after the list, because
markdownlint's MD013 exempts definition lines. The tool owns the "toc-"
label prefix: it removes "[toc-...]: #..." definitions elsewhere in the file.

Usage: markdown_toc.py [--check] [--max-level N] [--width N] FILE [FILE ...]
Exit status: 0 lists current (or rewritten), 1 --check found a stale list,
2 bad input (missing file, no "## Contents" heading, or text other than
a list in the Contents section); other files are still processed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
LIST_ITEM = re.compile(r"^\s*[-*+] ")
TOC_DEFINITION = re.compile(r"^ {0,3}\[toc-[^\]]+\]:[ \t]*#")
CONTENTS = "Contents"


class InputError(Exception):
    pass


def github_slug(heading: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", heading.strip().lower())
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def link_text(heading: str) -> str:
    """Heading text usable inside a link: nested links become their text."""
    return re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading.strip())


def prose_lines(lines: list[str]) -> list[bool]:
    """True for each line outside fenced code (fence lines are False)."""
    flags: list[bool] = []
    opener = ""
    for line in lines:
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            rest = line.strip()[len(marker) :].strip()
            if not opener:
                opener = marker
            elif marker[0] == opener[0] and len(marker) >= len(opener) and not rest:
                opener = ""
            flags.append(False)
            continue
        flags.append(not opener)
    return flags


def heading_lines(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line index, level, text) for each heading outside fenced code."""
    found: list[tuple[int, int, str]] = []
    for index, (line, prose) in enumerate(zip(lines, prose_lines(lines), strict=True)):
        match = HEADING.match(line) if prose else None
        if match:
            found.append((index, len(match.group(1)), match.group(2)))
    return found


def drop_toc_definitions(lines: list[str]) -> list[str]:
    """Remove "[toc-...]: #..." lines outside fences and the blank they leave."""
    kept: list[str] = []
    removed = False
    for line, prose in zip(lines, prose_lines(lines), strict=True):
        if prose and TOC_DEFINITION.match(line):
            removed = True
            continue
        if removed and not line.strip() and kept and not kept[-1].strip():
            continue
        removed = False
        kept.append(line)
    while len(kept) > 1 and not kept[-1].strip() and not kept[-2].strip():
        kept.pop()
    return kept


def build(text: str, max_level: int, width: int = 80) -> str:
    """Return the text with its Contents list rebuilt."""
    lines = text.split("\n")
    found = heading_lines(lines)
    starts = [
        i
        for i, (_, level, title) in enumerate(found)
        if (level, title) == (2, CONTENTS)
    ]
    if not starts:
        raise InputError("no '## Contents' heading")
    position = starts[0]
    begin = found[position][0] + 1
    end = found[position + 1][0] if position + 1 < len(found) else len(lines)
    body = [line for line in lines[begin:end] if line.strip()]
    if any(not (LIST_ITEM.match(line) or TOC_DEFINITION.match(line)) for line in body):
        raise InputError("the Contents section holds text other than a list")

    entries: list[str] = []
    definitions: list[str] = []
    counts: dict[str, int] = {}
    for i, (_, level, title) in enumerate(found):
        slug = github_slug(title)
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        if i == position or not 2 <= level <= max_level:
            continue
        anchor = slug if seen == 0 else f"{slug}-{seen}"
        entry = f"{'  ' * (level - 2)}- [{link_text(title)}]"
        if len(entry) + len(anchor) + 3 > width:
            label = f"toc-{len(definitions) + 1}"
            definitions.append(f"[{label}]: #{anchor}")
            entries.append(f"{entry}[{label}]")
        else:
            entries.append(f"{entry}(#{anchor})")

    section = ["", *entries, *([""] if definitions else []), *definitions]
    tail = [""] if end < len(lines) else []
    before = drop_toc_definitions(lines[:begin])
    after = drop_toc_definitions(lines[end:])
    return "\n".join([*before, *section, *tail, *after])


EPILOG = """\
Examples:
  python3 scripts/markdown_toc.py docs/guide.md
  python3 scripts/markdown_toc.py --max-level 3 README.md
  python3 scripts/markdown_toc.py --check references/*.md
  python3 scripts/markdown_toc.py --width 100 notes.md
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Write or check the linked '## Contents' list of Markdown files.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", type=Path, metavar="FILE")
    parser.add_argument(
        "--check", action="store_true", help="report stale lists, change nothing"
    )
    parser.add_argument(
        "--max-level",
        type=int,
        default=2,
        help="deepest heading level listed (2-6, default 2)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help="longest inline entry before a reference link is used (default 80)",
    )
    args = parser.parse_args(argv)
    if not 2 <= args.max_level <= 6:
        parser.error("--max-level must be between 2 and 6")

    status = 0
    for path in args.files:
        try:
            text = path.read_text(encoding="utf-8")
            updated = build(text, args.max_level, args.width)
        except (OSError, InputError) as error:
            print(f"{path}: {error}", file=sys.stderr)
            status = 2
            continue
        if updated == text:
            continue
        if args.check:
            print(f"{path}: Contents list is stale")
            status = max(status, 1)
        else:
            path.write_text(updated, encoding="utf-8")
            print(f"{path}: Contents list rewritten")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
