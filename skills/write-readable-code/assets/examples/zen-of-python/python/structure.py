"""Simple over complex, complex over complicated, flat over nested, and
special cases that follow the general rule.

`structure_before.py` holds the replaced versions; the tests prove each
pair behaves the same on every input they enumerate.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


def format_price(cents: int, currency: str) -> str:
    """One function replaces a one-implementation strategy hierarchy."""
    symbol = {"EUR": "€", "USD": "$"}[currency]
    return f"{symbol}{cents // 100}.{cents % 100:02d}"


def retry(
    operation: Callable[[], T],
    *,
    attempts: int,
    retry_on: type[Exception],
    delays: Iterable[float],
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run operation, retrying retry_on errors after each delay in turn.

    The complexity (attempt count, which errors, backoff) lives here once
    instead of as sleep-and-try blocks at every call site.
    """
    pauses = iter(delays)
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_on:
            if attempt == attempts:
                raise
            sleep(next(pauses))
    raise ValueError("attempts must be at least 1")


@dataclass(frozen=True)
class Order:
    paid: bool
    items: int
    address: str | None


def shipping_label(order: Order) -> str:
    """Guard clauses keep the success path at one indentation level."""
    if not order.paid:
        return "hold: unpaid"
    if order.items == 0:
        return "hold: empty"
    if order.address is None:
        return "hold: no address"
    return f"ship {order.items} item(s) to {order.address}"


def chunks(items: Sequence[T], size: int) -> list[list[T]]:
    """Empty input and a short last chunk follow the general rule."""
    if size < 1:
        raise ValueError("size must be at least 1")
    return [list(items[i : i + size]) for i in range(0, len(items), size)]
