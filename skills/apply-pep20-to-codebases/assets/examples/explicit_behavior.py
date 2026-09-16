"""Executable examples of explicit defaults, exceptions, and resource ownership.

These functions have narrow contracts; they are examples, not a new framework.
Python 3.10+. The tests intentionally distinguish valid falsey values and
errors from different operations.
"""

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO, TypeVar

T = TypeVar("T")
_MISSING = object()


def effective_timeout(value: float | None, default: float) -> float:
    """Only None means unspecified. Zero remains an explicit value."""
    return default if value is None else value


def option(options: Mapping[str, object], name: str, default: object) -> object:
    """Missing key uses the default; present None, False, 0, and '' survive."""
    value = options.get(name, _MISSING)
    return default if value is _MISSING else value


def render_named(
    renderers: Mapping[str, Callable[[T], str]], name: str, value: T
) -> str:
    """Translate lookup failure, not errors raised by the chosen renderer."""
    try:
        render = renderers[name]
    except KeyError as exc:
        raise ValueError(f"unknown renderer: {name}") from exc
    return render(value)


def nonempty_lines(stream: TextIO) -> Iterator[str]:
    """Borrow the stream: do not close a caller-owned resource."""
    for line in stream:
        text = line.rstrip("\r\n")
        if text:
            yield text


@contextmanager
def open_nonempty_lines(path: Path) -> Iterator[Iterator[str]]:
    """Own the file until the with block exits, including partial consumption."""
    with path.open(encoding="utf-8") as stream:
        yield nonempty_lines(stream)
