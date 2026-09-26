"""Counterexamples for the plan under review, and their corrections.

`naive_update` is what the plan describes. The tests in
tests/test_config_store.py drive exact interleavings to show its flaws.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable


def naive_update(
    path: Path,
    edits: dict[str, object],
    between: Callable[[], None] = lambda: None,
) -> None:
    current = json.loads(path.read_text())
    between()  # another writer may run here
    current.update(edits)
    with open(path, "w", encoding="utf-8") as handle:  # truncates first
        handle.write(json.dumps(current))


class StaleWriteError(RuntimeError):
    """The file changed after it was read; re-read and re-apply the edits."""


def versioned_update(
    path: Path,
    edits: dict[str, object],
    between: Callable[[], None] = lambda: None,
) -> None:
    before = path.stat().st_mtime_ns, path.read_bytes()
    current = json.loads(before[1])
    between()
    current.update(edits)
    payload = json.dumps(current)  # serialize fully before touching disk
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    if (path.stat().st_mtime_ns, path.read_bytes()) != before:
        temporary.unlink()
        raise StaleWriteError(str(path))
    os.replace(temporary, path)
