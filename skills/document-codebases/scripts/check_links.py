#!/usr/bin/env python3
"""Check relative links, heading anchors, and link text in Markdown files.

Errors:
  - a relative link or image whose file does not exist;
  - a #fragment that matches no heading in the target file (anchors are
    computed like GitHub: lowercase, punctuation removed, spaces to
    hyphens, repeated headings suffixed -1, -2, ...);
  - a [text][label] reference with no [label]: definition.
Warnings:
  - link text that says nothing about the target ("here", "click here",
    "link", "this"); an image with empty alt text.
External URLs (http, https, mailto) are listed with --external but not
fetched: a 200 status can still be a login page, so check them by hand.
Links inside fenced code blocks and inline code are ignored.

Usage: check_links.py PATH... [--external] [--json]
Exit status: 0 no errors, 1 errors, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

FENCE = re.compile(r"^(```+|~~~+)")
INLINE_CODE = re.compile(r"(`+).*?\1")
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REF_USE = re.compile(r"(!?)\[([^\]]+)\]\[([^\]]*)\]")
REF_DEF = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(\S+)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
VAGUE = {"here", "click here", "link", "this", "this link", "read more"}
EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  unreadable input: a PATH does not exist or a file is not UTF-8

Output: "error: FILE:LINE: ..." and "warning: FILE:LINE: ..." lines, then
"N error(s), N warning(s)"; with --external, "external FILE:LINE: URL"
lines come first. --json prints {"errors": [...], "warnings": [...],
"external": [...]}, each entry {file, line, message} (external entries
carry the URL as message; the list is empty without --external).

Examples:
  python3 scripts/check_links.py README.md docs
  python3 scripts/check_links.py docs --external
  python3 scripts/check_links.py docs --json | jq '.errors[].message'
"""


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Lines outside fenced code, with inline code removed."""
    result, fence = [], None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line.lstrip())
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker.startswith(fence[0]) and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None:
            result.append((number, INLINE_CODE.sub("", line)))
    return result


def slug(heading: str) -> str:
    """GitHub-style anchor: link text kept, code marks and punctuation
    removed (underscores stay, since \\w includes them), spaces to hyphens."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading.strip().lower())
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    found = set()
    for _, line in prose_lines(path.read_text(encoding="utf-8")):
        match = HEADING.match(line)
        if not match:
            continue
        base = slug(match.group(1))
        count = seen.get(base, 0)
        found.add(base if count == 0 else f"{base}-{count}")
        seen[base] = count + 1
    return found


def check_file(path: Path, external: bool) -> tuple[list[str], list[str]]:
    errors, warnings, links = findings(path)
    if external:
        for link in links:
            print(f"external {link['file']}:{link['line']}: {link['message']}")
    return [describe(e) for e in errors], [describe(w) for w in warnings]


def describe(finding: dict) -> str:
    return f"{finding['file']}:{finding['line']}: {finding['message']}"


def findings(path: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """Errors, warnings, and external links of one file, as
    {file, line, message} records (an external link's message is its URL)."""
    errors: list[dict] = []
    warnings: list[dict] = []
    links: list[dict] = []

    def at(number: int, message: str) -> dict:
        return {"file": str(path), "line": number, "message": message}

    lines = prose_lines(path.read_text(encoding="utf-8"))
    definitions = {}
    for _, line in lines:
        match = REF_DEF.match(line)
        if match:
            definitions[match.group(1).lower()] = match.group(2)
    targets: list[tuple[int, str, str, bool]] = []
    for number, line in lines:
        if REF_DEF.match(line):
            _, target = REF_DEF.match(line).groups()  # type: ignore[union-attr]
            targets.append((number, "", target, False))
            continue
        for bang, text, target in LINK.findall(line):
            targets.append((number, text, target, bang == "!"))
        for _bang, text, label in REF_USE.findall(line):
            key = (label or text).lower()
            if key not in definitions:
                errors.append(at(number, f"undefined reference [{label or text}]"))
            elif text.strip().lower() in VAGUE:
                warnings.append(at(number, f"vague link text {text!r}"))
    for number, text, target, image in targets:
        if image and not text.strip():
            warnings.append(at(number, f"image without alt text: {target}"))
        if not image and text and text.strip().lower() in VAGUE:
            warnings.append(at(number, f"vague link text {text!r}"))
        if re.match(r"^[a-z][a-z0-9+.-]*:", target):
            links.append(at(number, target))
            continue
        file_part, _, fragment = target.partition("#")
        destination = (
            (path.parent / unquote(file_part)).resolve()
            if file_part
            else path.resolve()
        )
        if not destination.exists():
            errors.append(at(number, f"missing target {file_part}"))
            continue
        same_file = destination == path.resolve()
        checkable = destination.suffix.lower() == ".md" or same_file
        known = anchors(destination) if checkable and destination.is_file() else None
        if fragment and known is not None and unquote(fragment).lower() not in known:
            errors.append(
                at(number, f"no heading for #{fragment} in {destination.name}")
            )
    return errors, warnings, links


def markdown_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files += sorted(path.rglob("*.md"))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(
                f"{raw} does not exist; pass Markdown files or directories"
            )
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths", nargs="+", help="Markdown files, or directories to search for *.md"
    )
    parser.add_argument(
        "--external", action="store_true", help="also list external URLs (not fetched)"
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    found: list[tuple[list[dict], list[dict], list[dict]]] = []
    results: list[tuple[list[str], list[str]]] = []
    try:
        if args.json:
            found = [findings(f) for f in markdown_files(args.paths)]
        else:
            results = [check_file(f, args.external) for f in markdown_files(args.paths)]
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        report = {
            "errors": [e for errors, _, _ in found for e in errors],
            "warnings": [w for _, warnings, _ in found for w in warnings],
            "external": [x for _, _, links in found for x in links]
            if args.external
            else [],
        }
        print(json.dumps(report, indent=2))
        return 1 if report["errors"] else 0
    errors = [e for found, _ in results for e in found]
    warnings = [w for _, found in results for w in found]
    for message in errors:
        print(f"error: {message}")
    for message in warnings:
        print(f"warning: {message}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
