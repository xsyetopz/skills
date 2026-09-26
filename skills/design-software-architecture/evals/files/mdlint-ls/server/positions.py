"""Convert positions inside a line between Python and LSP."""


def to_lsp_character(line_text: str, index: int) -> int:
    """Return the LSP `character` value for the Python str index `index`."""
    return index
