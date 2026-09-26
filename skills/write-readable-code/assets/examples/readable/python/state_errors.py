"""Explicit state, dependencies, and error flow."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from typing import Callable

# --- Explicit dependencies instead of ambient state ---------------------

_SETTINGS: dict[str, int] = {"grace_days": 3}


def baseline_is_overdue(due: dt.date) -> bool:
    # Reads a module global and the wall clock: the result depends on
    # state the signature does not show, and tests cannot pin "today".
    grace = dt.timedelta(days=_SETTINGS["grace_days"])
    return dt.date.today() > due + grace


def candidate_is_overdue(due: dt.date, today: dt.date, grace_days: int) -> bool:
    return today > due + dt.timedelta(days=grace_days)


# --- Side effects at the edge (pure core, imperative shell) -------------


def baseline_summarize_and_save(scores: list[int], path: str) -> None:
    total = 0
    for score in scores:
        total += score
    average = total / len(scores) if scores else 0.0
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"count": len(scores), "average": average}, handle)


@dataclass(frozen=True)
class ScoreSummary:
    count: int
    average: float


def summarize(scores: list[int]) -> ScoreSummary:
    average = sum(scores) / len(scores) if scores else 0.0
    return ScoreSummary(count=len(scores), average=average)


def save_summary(summary: ScoreSummary, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"count": summary.count, "average": summary.average}, handle)


# --- Visible, specific error handling ------------------------------------


class ConfigError(Exception):
    """Configuration could not be loaded; the message names the file."""


def baseline_load_port(read_text: Callable[[str], str], path: str) -> int:
    try:
        return int(json.loads(read_text(path))["port"])
    except Exception:  # noqa: BLE001 - deliberate anti-pattern
        return 8080  # hides a missing file, bad JSON, and a typo alike


def candidate_load_port(read_text: Callable[[str], str], path: str) -> int:
    try:
        document = json.loads(read_text(path))
    except FileNotFoundError:
        return 8080  # documented default when no config file exists
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path}: invalid JSON: {error}") from error

    try:
        return int(document["port"])
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigError(f"{path}: 'port' must be an integer") from error
