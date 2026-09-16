"""Read the bounded Markdown profile used by the changelog validators."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

ATX_HEADING = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$")
SETEXT_UNDERLINE = re.compile(r" {0,3}(=+|-+)[ \t]*$")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)$")
LINK = re.compile(r"!?\[([^]]*)\]\([^\n)]*(?:\)[^\n)]*)?\)")
REFERENCE_LINK = re.compile(r"!?\[([^]]*)\]\[[^]]*\]")
LINK_DEFINITION = re.compile(r" {0,3}\[[^]]+\]:[ \t]*\S+")
LIST_MARKER = re.compile(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])[ \t]+")
THEMATIC_BREAK = re.compile(
    r" {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})"
)
ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
CODE_SPAN = re.compile(r"(`+)(.+?)\1")
HTML_BLOCK = re.compile(
    r" {0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|"
    r"center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|"
    r"figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|"
    r"legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|"
    r"param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|"
    r"track|ul)(?:[ \t]|/?>|$)",
    re.IGNORECASE,
)


@dataclass
class Section:
    level: int
    title: str
    line: int
    has_content: bool = False


def inline_text(source: str) -> str:
    """Return visible text for the inline constructs relevant to headings."""
    source = CODE_SPAN.sub(lambda match: match.group(2).strip(" "), source)
    previous = None
    while source != previous:
        previous = source
        source = LINK.sub(lambda match: match.group(1), source)
        source = REFERENCE_LINK.sub(lambda match: match.group(1), source)
    source = ESCAPE.sub(r"\1", source)
    return html.unescape(source).strip()


def heading(line: str) -> tuple[int, str] | None:
    match = ATX_HEADING.fullmatch(line)
    if not match:
        return None
    title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2) or "")
    return len(match.group(1)), inline_text(title)


def sections(text: str) -> list[Section]:
    """Extract top-level headings and whether their bodies contain content.

    This is intentionally not a general Markdown parser. It recognizes the
    CommonMark block forms that affect the changelog profile and ignores
    headings in fences, indented code, HTML comments, lists, and blockquotes.
    """
    result: list[Section] = []
    lines = text.splitlines()
    fence: tuple[str, int] | None = None
    in_comment = False
    in_html_block = False
    index = 0

    def mark_content(source: str) -> None:
        if (
            not result
            or LINK_DEFINITION.fullmatch(source)
            or THEMATIC_BREAK.fullmatch(source)
        ):
            return
        source = LIST_MARKER.sub("", source, count=1)
        result[-1].has_content |= bool(inline_text(source))

    while index < len(lines):
        line = lines[index]

        if in_html_block:
            if not line.strip():
                in_html_block = False
            index += 1
            continue

        if fence:
            marker, length = fence
            if re.fullmatch(rf" {{0,3}}{re.escape(marker)}{{{length},}}[ \t]*", line):
                fence = None
            else:
                mark_content(line)
            index += 1
            continue

        fence_match = FENCE.fullmatch(line)
        if fence_match and not (
            fence_match.group(1).startswith("`") and "`" in fence_match.group(2)
        ):
            delimiter = fence_match.group(1)
            fence = delimiter[0], len(delimiter)
            index += 1
            continue

        stripped = line.lstrip(" ")
        if in_comment:
            if "-->" in line:
                in_comment = False
            index += 1
            continue
        if len(line) - len(stripped) <= 3 and stripped.startswith("<!--"):
            in_comment = "-->" not in stripped
            index += 1
            continue

        if HTML_BLOCK.match(line):
            in_html_block = True
            index += 1
            continue

        if line.startswith(("    ", "\t")):
            mark_content(line[1:] if line.startswith("\t") else line[4:])
            index += 1
            continue

        parsed_heading = heading(line)
        if parsed_heading:
            level, title = parsed_heading
            result.append(Section(level, title, index + 1))
            index += 1
            continue

        nested = line
        while True:
            reduced = re.sub(r"^ {0,3}>[ \t]?", "", nested, count=1)
            reduced = LIST_MARKER.sub("", reduced, count=1)
            if reduced == nested:
                break
            nested = reduced
        if nested != line and heading(nested):
            index += 1
            continue

        if index + 1 < len(lines):
            underline = SETEXT_UNDERLINE.fullmatch(lines[index + 1])
            if (
                underline
                and line.strip()
                and not line.startswith((">", "- ", "+ ", "* "))
            ):
                level = 1 if underline.group(1).startswith("=") else 2
                result.append(Section(level, inline_text(line.strip()), index + 1))
                index += 2
                continue

        mark_content(line)
        index += 1

    return result


def release_header(title: str) -> tuple[str, str]:
    """Split the displayed release label and date; leave invalid values for audit."""
    version, separator, released = title.partition(" - ")
    if version.startswith("[") and version.endswith("]"):
        version = version[1:-1]
    return version, released.removesuffix(" [YANKED]") if separator else ""
