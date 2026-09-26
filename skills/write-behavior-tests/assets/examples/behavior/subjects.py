"""Code under test for every card. Each function states its contract.

variants.py replaces single attributes with conforming alternatives or
deliberate faults; harness.load() applies the variant named by $VARIANT.
"""

from __future__ import annotations

import base64
import os
import sqlite3
import threading
from collections import Counter
from collections.abc import Callable, Mapping
from pathlib import Path


# --- test structure -------------------------------------------------------
def shipping(weight_kg: float) -> int:
    """Zero weight ships free; any positive weight costs a flat 5."""
    if weight_kg < 0:
        raise ValueError("weight must not be negative")
    return 0 if weight_kg == 0 else 5


PRICES = {"book": 20, "pen": 2}


class Cart:
    """Totals the listed price of every added item."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def add(self, item: str) -> None:
        self._items.append(item)

    def remove(self, item: str) -> None:
        self._items.remove(item)

    @property
    def total(self) -> int:
        return sum(PRICES[item] for item in self._items)


class Connection:
    """open() after close() must succeed: a connection can be reused."""

    def __init__(self) -> None:
        self.is_open = False

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False


# --- oracles and inputs ---------------------------------------------------
def invoice_total(price: int, quantity: int, discount: int) -> int:
    """Cents: price times quantity, less one invoice-level discount."""
    return price * quantity - discount


def accept_percentage(value: int) -> bool:
    """Valid percentages are the integers 1 through 100 inclusive."""
    return 1 <= value <= 100


def can_edit(role: str, account: str) -> bool:
    """Editors and admins may edit active accounts; admins also suspended."""
    if role == "admin":
        return account in {"active", "suspended"}
    return role == "editor" and account == "active"


TRANSITIONS = {
    ("draft", "submit"): "review",
    ("review", "approve"): "published",
    ("review", "reject"): "draft",
    ("published", "archive"): "archived",
}


def next_state(state: str, event: str) -> str:
    """Documented transitions only; anything else raises ValueError."""
    try:
        return TRANSITIONS[(state, event)]
    except KeyError:
        raise ValueError(f"{event!r} not allowed in {state!r}") from None


def b64encode(data: bytes) -> str:
    """RFC 4648 section 4 base64 with padding."""
    return base64.b64encode(data).decode("ascii")


def b64decode(text: str) -> bytes:
    return base64.b64decode(text, validate=True)


def render_report(rows: list[tuple[str, int]], generated_at: str) -> str:
    """Stable text report; generated_at is the only volatile field."""
    lines = [f"generated: {generated_at}", "name,count"]
    lines += [f"{name},{count}" for name, count in sorted(rows)]
    return "\n".join(lines) + "\n"


# --- coupling and doubles -------------------------------------------------
def _trim(text: str) -> str:
    return text.strip()


def render_name(text: str) -> str:
    """Display name without surrounding whitespace."""
    return _trim(text)


class Basket:
    """count(item) is how many times item was added."""

    def __init__(self) -> None:
        self._items: list[str] = []

    def add(self, item: str) -> None:
        self._items.append(item)

    def count(self, item: str) -> int:
        return self._items.count(item)


def price_for(item: str, catalog: Mapping[str, int]) -> int:
    """Listed price of item; KeyError when it is not listed."""
    if item not in catalog:
        raise KeyError(item)
    return catalog[item]


def notify(address: str, allowed: bool, send: Callable[[str, str], None]) -> bool:
    """Send exactly one "ready" message to allowed addresses; none otherwise."""
    if not allowed:
        return False
    send(address, "ready")
    return True


class Users:
    """Emails are unique, compared case-insensitively."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.db = connection
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            " id INTEGER PRIMARY KEY,"
            " email TEXT NOT NULL UNIQUE COLLATE NOCASE)"
        )

    def add(self, email: str) -> int:
        cursor = self.db.execute("INSERT INTO users (email) VALUES (?)", (email,))
        return int(cursor.lastrowid or 0)


# --- regressions and nondeterminism ---------------------------------------
def split_fields(line: str) -> list[str]:
    """Split on ':' keeping empty fields: 'a::b' has three fields."""
    return line.split(":")


def write_config(path: Path, text: str) -> None:
    """Replace path with text only if text parses; else leave it untouched."""
    if "=" not in text:
        raise ValueError("config must contain key=value lines")
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


class Account:
    """deposit() is safe to call from several threads."""

    def __init__(self) -> None:
        self.balance = 0
        self._lock = threading.Lock()
        self.before_write: Callable[[], None] = lambda: None

    def deposit(self, amount: int) -> None:
        with self._lock:
            current = self.balance
            self.before_write()  # test hook: widen the race window
            self.balance = current + amount


class Session:
    """Expires ttl seconds after creation, measured by the injected clock."""

    def __init__(self, ttl: float, clock: Callable[[], float]) -> None:
        self.clock = clock
        self.expires_at = clock() + ttl

    @property
    def expired(self) -> bool:
        return self.clock() >= self.expires_at


_SEEN: Counter[str] = Counter()


def register(name: str) -> int:
    """Returns how many times name was registered in this process."""
    _SEEN[name] += 1
    return _SEEN[name]


def reset_registry() -> None:
    _SEEN.clear()


DELIVERY_FEES = [5]


def delivery_fee(distance_km: int) -> int:
    """Flat fee of 5 for any distance."""
    del distance_km
    return DELIVERY_FEES[0]
