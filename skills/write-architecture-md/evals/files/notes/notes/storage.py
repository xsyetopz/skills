"""Reads and writes the notebook file. The only module that does file I/O."""

import json
import os
from pathlib import Path


def default_path() -> Path:
    return Path(os.environ.get("NOTES_FILE", Path.home() / ".notes.json"))


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, notes: list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(notes, indent=2), encoding="utf-8")
    tmp.replace(path)
