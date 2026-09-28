"""slugkit at HEAD (unreleased). Public API: slugify()."""

import re


def slugify(text: str, max_length: int = 80, separator: str = "-") -> str:
    """Lowercase text, replace non-alphanumerics with separator, trim."""
    slug = re.sub(r"[^a-z0-9]+", separator, text.lower()).strip(separator)
    return slug[:max_length].rstrip(separator)
