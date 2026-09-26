"""Domain rules. Imports nothing from adapters or the standard library's I/O."""

from __future__ import annotations

from dataclasses import dataclass


class OrderError(ValueError):
    """A request that violates a domain rule."""


@dataclass(frozen=True)
class Order:
    order_id: str
    customer: str
    items: tuple[tuple[str, int], ...]

    @property
    def quantity(self) -> int:
        return sum(count for _, count in self.items)


def new_order(order_id: str, customer: str, items: dict[str, int]) -> Order:
    if not customer:
        raise OrderError("customer is required")
    if not items or any(count <= 0 for count in items.values()):
        raise OrderError("items need positive counts")
    return Order(order_id, customer, tuple(sorted(items.items())))
