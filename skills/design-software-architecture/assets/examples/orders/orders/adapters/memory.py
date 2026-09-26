"""In-memory adapter for tests and demos."""

from __future__ import annotations

from orders.domain import Order


class MemoryStore:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._keys: dict[str, str] = {}

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def get_by_key(self, idempotency_key: str) -> Order | None:
        order_id = self._keys.get(idempotency_key)
        return self._orders.get(order_id) if order_id else None

    def add(self, order: Order, idempotency_key: str) -> Order:
        if idempotency_key in self._keys:
            return self._orders[self._keys[idempotency_key]]
        self._orders[order.order_id] = order
        self._keys[idempotency_key] = order.order_id
        return order
