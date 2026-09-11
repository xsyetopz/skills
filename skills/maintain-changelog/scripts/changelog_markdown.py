"""Read top-level changelog sections using CommonMark, not source-line regexes."""

from dataclasses import dataclass

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass
class Section:
    level: int
    title: str
    line: int
    has_content: bool = False


def inline_text(token: Token) -> str:
    return "".join(child.content for child in token.children or []).strip()


def sections(text: str) -> list[Section]:
    result: list[Section] = []
    tokens = MarkdownIt("commonmark").parse(text)
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.level == 0:
            # Heading tokens always have a source map and a following inline token.
            assert token.map is not None
            result.append(
                Section(
                    int(token.tag[1:]), inline_text(tokens[index + 1]), token.map[0] + 1
                )
            )
        elif (
            result
            and token.type == "inline"
            and tokens[index - 1].type != "heading_open"
        ):
            result[-1].has_content |= bool(inline_text(token))
        elif result and token.type in {"fence", "code_block"}:
            result[-1].has_content |= bool(token.content.strip())
    return result


def release_header(title: str) -> tuple[str, str]:
    """Split the displayed release label and date; leave invalid values for audit."""
    version, separator, released = title.partition(" - ")
    if version.startswith("[") and version.endswith("]"):
        version = version[1:-1]
    return version, released.removesuffix(" [YANKED]") if separator else ""
