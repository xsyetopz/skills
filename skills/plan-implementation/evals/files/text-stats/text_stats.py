"""Small text statistics used by the report generator."""


def line_count(text: str) -> int:
    return len(text.splitlines())
