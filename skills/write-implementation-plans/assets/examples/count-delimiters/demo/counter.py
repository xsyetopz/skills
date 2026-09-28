"""Delimiter counting for the worked plan (the candidate implementation).

The original implementation was `len(text.split(delimiter)) - 1`, which
allocates a list of pieces. `str.count` returns the same number without the
list, except for an empty delimiter, where `split` raises ValueError and
`count` returns len(text) + 1; the guard keeps the original contract.
"""


def count_delimiters(text: str, delimiter: str) -> int:
    if not delimiter:
        raise ValueError("empty separator")
    return text.count(delimiter)


def count_delimiters_split(text: str, delimiter: str) -> int:
    """The original implementation, kept as the test oracle."""
    return len(text.split(delimiter)) - 1
