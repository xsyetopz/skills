"""The port: what the application needs from storage, nothing more."""

from __future__ import annotations

from typing import Protocol

from orders.domain import Order


class OrderStore(Protocol):
    def get(self, order_id: str) -> Order | None: ...

    def get_by_key(self, idempotency_key: str) -> Order | None: ...

    def add(self, order: Order, idempotency_key: str) -> Order:
        """Store order; if the key exists, return the stored order instead."""
        ...
