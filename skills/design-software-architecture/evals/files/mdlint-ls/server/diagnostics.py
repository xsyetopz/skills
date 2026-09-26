"""Report lines with trailing whitespace as diagnostics."""

from server.positions import to_lsp_character


def trailing_whitespace(text: str) -> list[dict]:
    found = []
    for number, line in enumerate(text.splitlines()):
        stripped = line.rstrip()
        if stripped != line:
            found.append(
                {
                    "range": {
                        "start": {
                            "line": number,
                            "character": to_lsp_character(line, len(stripped)),
                        },
                        "end": {
                            "line": number,
                            "character": to_lsp_character(line, len(line)),
                        },
                    },
                    "message": "trailing whitespace",
                }
            )
    return found
