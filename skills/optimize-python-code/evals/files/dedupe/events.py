"""Event de-duplication used by the nightly reconciliation job."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class Event:
    id: int
    kind: str
    ts: int


def dedupe_events(events: Iterable[Event], blocked: list[int]) -> list[Event]:
    """Return events whose id is not blocked, dropping repeats.

    Two events are repeats when they compare equal. The first occurrence
    wins and the output keeps input order. `events` is usually a generator
    that streams rows from a database cursor.
    """
    out = []
    for e in events:
        if e.id not in blocked and e not in out:
            out.append(e)
    return out
