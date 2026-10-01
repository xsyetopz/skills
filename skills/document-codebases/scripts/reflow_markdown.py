#!/usr/bin/env python3
"""Reflow Markdown paragraphs so each line fills up to --width characters.

Only paragraph text is rewrapped, including paragraphs inside list items and
block quotes, which keep their marker and continuation indent. Everything
else is copied unchanged: YAML front matter, headings, fenced and indented
code, tables, HTML blocks, link reference definitions, thematic breaks, and
any paragraph with a hard line break (trailing backslash or two spaces, or
<br>). A paragraph directly above a setext underline is a heading and is
kept as well. Where a block boundary is unclear, the paragraph is ended
there, so lines are never joined across blocks.

Words are split at whitespace only. A code span stays on one line unless it
is longer than a whole line; then it is split at its spaces, which Markdown
renders as single spaces. A line never starts with a word that would begin a
new block (a list marker, "#", ">", "|", a fence, or "<"); the previous word
moves down with it instead. A single word longer than --width is left long.

Without --width, each file's width is MD013 line_length from the nearest
markdownlint config found upward from the file (.markdownlint-cli2.jsonc,
.markdownlint.jsonc, or .markdownlint.json, following local "extends"). A
config that enables MD013 without line_length means markdownlint's default
of 80. With no config, MD013 disabled, or a config format this script cannot
read (YAML, JavaScript), the width is 100, and the last case is reported.

Usage: reflow_markdown.py [--check] [--width N] FILE [FILE ...]
Exit status: 0 files current (or rewritten), 1 --check found a file to
reflow, 2 bad input (missing or unreadable file or config); other files are
still processed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FALLBACK_WIDTH = 100
MD013_DEFAULT = 80
CONFIG_NAMES = (
    ".markdownlint-cli2.jsonc",
    ".markdownlint-cli2.yaml",
    ".markdownlint-cli2.cjs",
    ".markdownlint-cli2.mjs",
    ".markdownlint.jsonc",
    ".markdownlint.json",
    ".markdownlint.yaml",
    ".markdownlint.yml",
    ".markdownlint.cjs",
    ".markdownlint.mjs",
)
JSONC_NOISE = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.DOTALL)
TRAILING_COMMA = re.compile(r'("(?:\\.|[^"\\])*")|,(\s*[}\]])')

FENCE = re.compile(r"^ *(`{3,}|~{3,})")
QUOTE = re.compile(r"^ {0,3}> ?")
LIST_MARKER = re.compile(r"^( *)([-*+]|\d{1,9}[.)])( +|$)")
HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
SETEXT = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
THEMATIC = re.compile(r"^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:")
# "<" opening an HTML block; an autolink such as <https://example.com> does not.
NOT_AUTOLINK = r"(?![A-Za-z][A-Za-z0-9+.-]{1,31}:|[^\s<>@]+@)"
HTML_START = re.compile(r"^ {0,3}<" + NOT_AUTOLINK + r"[A-Za-z/!?]")
TABLE_DELIMITER = re.compile(r"^ *\|? *:?-+:? *(?:\| *:?-+:? *)*\|? *$")
HARD_BREAK = re.compile(r"(?:\\|  )$|<br\s*/?>", re.IGNORECASE)
# A word that would open a block if it started a line.
LINE_START_DANGER = re.compile(
    r"^(?:[-*+]$|\d{1,9}[.)]$|#{1,6}$|>|\||`{3}|~{3}|<"
    + NOT_AUTOLINK
    + r"|=+$|-+$|\*{3,}$|_{3,}$)"
)


def split_quote(line: str) -> tuple[str, str]:
    """(block quote markers, rest of the line)."""
    prefix = ""
    while True:
        match = QUOTE.match(line)
        if not match:
            return prefix, line
        prefix += match.group(0)
        line = line[match.end() :]


def words(text: str) -> list[str]:
    """Whitespace-separated words; a code span with spaces is one word."""
    found: list[str] = []
    current = ""
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            current += text[i : i + 2]
            i += 2
            continue
        if char == "`":
            run = len(text[i:]) - len(text[i:].lstrip("`"))
            close = re.compile(r"(?<!`)" + "`" * run + r"(?!`)")
            end = close.search(text, i + run)
            if end:
                current += re.sub(r"\s+", " ", text[i : end.end()])
                i = end.end()
                continue
            current += text[i : i + run]
            i += run
            continue
        if char.isspace():
            if current:
                found.append(current)
                current = ""
        else:
            current += char
        i += 1
    if current:
        found.append(current)
    return found


def wrap(items: list[str], first: str, rest: str, width: int) -> list[str]:
    room = width - len(rest)
    pieces = [part for w in items for part in (w.split(" ") if len(w) > room else [w])]
    lines: list[str] = []
    current: list[str] = []
    prefix = first
    for word in pieces:
        if current and len(prefix + " ".join([*current, word])) > width:
            carried: list[str] = []
            while LINE_START_DANGER.match((carried or [word])[0]) and len(current) > 1:
                carried.insert(0, current.pop())
            if LINE_START_DANGER.match((carried or [word])[0]):
                current.append(word)
                continue
            lines.append(prefix + " ".join(current))
            current, prefix = [*carried, word], rest
        else:
            current.append(word)
    lines.append(prefix + " ".join(current))
    return lines


def classify(lines: list[str]) -> list[bool]:
    """True for each line that may be part of a paragraph."""
    flags = [False] * len(lines)
    fence = ""
    html_end = ""
    code_indent = -1
    containers: list[int] = [0]
    blank_before = True
    for index, raw in enumerate(lines):
        quote, line = split_quote(raw)
        stripped = line.strip()
        if fence:
            match = FENCE.match(line)
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = "" if not line.strip()[len(match.group(1)) :].strip() else fence
            continue
        if html_end:
            if (html_end == "\n" and not stripped) or (
                html_end != "\n" and html_end in line
            ):
                html_end = ""
            blank_before = not stripped
            continue
        if not stripped:
            blank_before = True
            continue
        indent = len(line) - len(line.lstrip(" "))
        if code_indent >= 0 and indent >= code_indent:
            continue
        code_indent = -1
        marker = LIST_MARKER.match(line)
        if blank_before and not quote:
            while len(containers) > 1 and indent < containers[-1]:
                containers.pop()
            if not marker and indent >= containers[-1] + 4:
                code_indent = containers[-1] + 4
                blank_before = False
                continue
        if marker and not quote:
            while len(containers) > 1 and indent < containers[-1]:
                containers.pop()
            containers.append(len(marker.group(0)) if marker.group(3) else indent + 2)
        blank_before = False
        body = line[marker.end() :] if marker else line
        if FENCE.match(body):
            fence = FENCE.match(body).group(1)  # type: ignore[union-attr]
            continue
        if HTML_START.match(body.lstrip()):
            html_end = "-->" if body.lstrip().startswith("<!--") else "\n"
            if html_end in body[body.find("<!--") + 4 :]:
                html_end = ""
            continue
        nxt = lines[index + 1] if index + 1 < len(lines) else ""
        if (
            HEADING.match(body)
            or THEMATIC.match(body)
            or SETEXT.match(body)
            or DEFINITION.match(body)
            or body.lstrip().startswith("|")
            or (
                "|" in body
                and TABLE_DELIMITER.match(split_quote(nxt)[1])
                and "-" in nxt
            )
            or (
                index
                and not flags[index - 1]
                and TABLE_DELIMITER.match(body)
                and "|" in body
            )
        ):
            continue
        flags[index] = True
    return flags


def paragraphs(lines: list[str], flags: list[bool]) -> list[tuple[int, int]]:
    """[start, end) line ranges of paragraphs."""
    found: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        if not flags[index]:
            index += 1
            continue
        start = index
        depth = split_quote(lines[index])[0].count(">")
        index += 1
        while index < len(lines) and flags[index]:
            quote, body = split_quote(lines[index])
            if quote.count(">") != depth or LIST_MARKER.match(body):
                break
            index += 1
        found.append((start, index))
    return found


def reflow(text: str, width: int) -> str:
    lines = text.split("\n")
    start = 0
    if lines and lines[0] == "---" and "---" in lines[1:]:
        start = lines.index("---", 1) + 1
    body = lines[start:]
    flags = classify(body)
    for begin, end in reversed(paragraphs(body, flags)):
        if end < len(body) and SETEXT.match(split_quote(body[end])[1]):
            continue
        block = body[begin:end]
        if any(HARD_BREAK.search(line) for line in block):
            continue
        quote, first_body = split_quote(block[0])
        lead = re.match(r" *", first_body).group(0)  # type: ignore[union-attr]
        marker = LIST_MARKER.match(first_body)
        first = quote + (marker.group(0) if marker else lead)
        if marker and not marker.group(3):
            continue
        rest = quote + " " * (len(first) - len(quote))
        text_parts = [block[0][len(first) :]] + [
            split_quote(line)[1] for line in block[1:]
        ]
        body[begin:end] = wrap(words(" ".join(text_parts)), first, rest, width)
    return "\n".join(lines[:start] + body)


def load_jsonc(path: Path) -> dict:
    text = JSONC_NOISE.sub(lambda m: m.group(1) or "", path.read_text(encoding="utf-8"))
    try:
        data = json.loads(TRAILING_COMMA.sub(lambda m: m.group(1) or m.group(2), text))
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level is not an object")
    return data


def md013_width(rules: dict, path: Path, seen: set[Path]) -> int | None:
    """MD013 line_length set by a markdownlint rules object; None when disabled."""
    for key in ("MD013", "line-length"):
        if key in rules:
            value = rules[key]
            if isinstance(value, dict):
                return int(value.get("line_length", MD013_DEFAULT))
            return MD013_DEFAULT if value else None
    extends = rules.get("extends")
    if isinstance(extends, str) and not re.match(r"^[a-z][a-z0-9+.-]*:", extends):
        parent = (path.parent / extends).resolve()
        if parent in seen:
            raise ValueError(f"extends cycle at {parent}")
        return md013_width(load_jsonc(parent), parent, seen | {parent})
    return MD013_DEFAULT if rules.get("default", True) else None


def configured_width(markdown: Path) -> tuple[int, str]:
    """(width, note) from the nearest markdownlint config above MARKDOWN."""
    for directory in markdown.resolve().parents:
        for name in CONFIG_NAMES:
            config = directory / name
            if not config.is_file():
                continue
            if config.suffix not in (".json", ".jsonc"):
                return (
                    FALLBACK_WIDTH,
                    f"cannot read {config}; using {FALLBACK_WIDTH}, pass --width",
                )
            rules = load_jsonc(config)
            if name.startswith(".markdownlint-cli2"):
                rules = rules.get("config", {})
            width = md013_width(rules, config, {config.resolve()})
            return (FALLBACK_WIDTH if width is None else width), ""
    return FALLBACK_WIDTH, ""


EPILOG = """\
Examples:
  python3 scripts/reflow_markdown.py README.md docs/*.md
  python3 scripts/reflow_markdown.py --check README.md
  python3 scripts/reflow_markdown.py --width 80 NOTES.md
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Reflow Markdown paragraphs to fill lines up to a width.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", type=Path, metavar="FILE")
    parser.add_argument(
        "--check", action="store_true", help="report files to reflow, change nothing"
    )
    parser.add_argument(
        "--width",
        type=int,
        help="longest line (default: MD013 line_length from markdownlint config, else 100)",
    )
    args = parser.parse_args(argv)
    if args.width is not None and args.width < 20:
        parser.error("--width must be at least 20")

    status = 0
    for path in args.files:
        try:
            text = path.read_text(encoding="utf-8")
            width, note = (args.width, "") if args.width else configured_width(path)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"{path}: {error}", file=sys.stderr)
            status = 2
            continue
        if note:
            print(f"{path}: {note}", file=sys.stderr)
        updated = reflow(text, max(width, 20))
        if updated == text:
            continue
        if args.check:
            print(f"{path}: needs reflow")
            status = max(status, 1)
        else:
            path.write_text(updated, encoding="utf-8")
            print(f"{path}: reflowed")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
