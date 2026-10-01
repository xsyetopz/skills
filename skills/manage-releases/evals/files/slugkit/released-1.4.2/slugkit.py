"""slugkit 1.4.2 as released. Public API: slugify()."""

import re


def slugify(text: str, max_len: int = 80) -> str:
    """Lowercase text, replace non-alphanumerics with '-', trim to max_len."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")
