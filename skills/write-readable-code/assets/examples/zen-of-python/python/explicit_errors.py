"""Explicit defaults, visible errors, narrow silencing, and refusing to guess.

Each function has one narrow contract that test_examples.py pins down,
including a mutant that the tests must reject. Python 3.10+.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from datetime import date
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


def remove_if_present(path: Path) -> None:
    """Silence exactly one expected error: the file is already gone."""
    with suppress(FileNotFoundError):
        os.remove(path)


def parse_release_date(text: str) -> date:
    """Accept only YYYY-MM-DD; '03/04/2025' is ambiguous and is rejected."""
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        raise ValueError(f"expected YYYY-MM-DD, got {text!r}")
    return date.fromisoformat(text)


def read_port(settings: Mapping[str, str]) -> int:
    """Refuse to pick one when the old and new key disagree."""
    new, old = settings.get("port"), settings.get("listen_port")
    if new is not None and old is not None and new != old:
        raise ValueError(f"port={new!r} conflicts with listen_port={old!r}")
    chosen = new if new is not None else old
    if chosen is None:
        raise KeyError("port")
    return int(chosen)


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
