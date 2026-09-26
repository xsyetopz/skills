"""Application service: uses the port, never a concrete adapter."""

from __future__ import annotations

import uuid

from orders.domain import Order, new_order
from orders.ports import OrderStore


def place_order(
    store: OrderStore, customer: str, items: dict[str, int], idempotency_key: str
) -> Order:
    """Create an order once per idempotency key; a retry returns the first."""
    existing = store.get_by_key(idempotency_key)
    if existing is not None:
        return existing
    order = new_order(uuid.uuid4().hex, customer, items)
    return store.add(order, idempotency_key)
