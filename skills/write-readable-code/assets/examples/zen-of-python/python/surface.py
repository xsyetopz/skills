"""One obvious way, deprecation now, a small public surface, namespaces,
a practical local mutation, and an implementation that is easy to explain.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Iterable, Mapping

__all__ = ["build_index", "is_power_of_two", "load_config", "read_config"]


def load_config(text: str) -> dict[str, object]:
    """The one supported way to parse configuration text."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("configuration must be a JSON object")
    return _with_defaults(data)


def read_config(text: str) -> dict[str, object]:
    """Deprecated alias of load_config; warns now, removed in 3.0."""
    warnings.warn(
        "read_config is deprecated; use load_config (removal in 3.0)",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_config(text)


def _with_defaults(data: Mapping[str, object]) -> dict[str, object]:
    """Private until a caller outside this module needs it."""
    return {"retries": 3, **data}


def build_index(words: Iterable[str]) -> dict[str, list[int]]:
    """Map each word to its positions.

    Local mutation of one dict is O(n); rebuilding an immutable mapping per
    word is O(n^2). The function stays pure from the caller's view.
    """
    index: dict[str, list[int]] = {}
    for position, word in enumerate(words):
        index.setdefault(word, []).append(position)
    return index


def is_power_of_two(n: int) -> bool:
    """A positive power of two has exactly one set bit, and n & (n - 1)
    clears the lowest set bit, so the result is zero only for such n."""
    return n > 0 and n & (n - 1) == 0
