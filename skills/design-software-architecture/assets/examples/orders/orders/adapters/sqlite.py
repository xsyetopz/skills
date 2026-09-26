"""SQLite adapter. The UNIQUE key makes concurrent retries safe too.

The adapter owns its connection's concurrency rule: sqlite3 connections
refuse use from another thread by default, and the threading HTTP server
calls from worker threads, so the adapter allows cross-thread use and
serializes every call with one lock.
"""

from __future__ import annotations

import json
import sqlite3
import threading

from orders.domain import Order


class SqliteStore:
    def __init__(self, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS orders ("
            " order_id TEXT PRIMARY KEY, customer TEXT NOT NULL,"
            " items TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE)"
        )

    def close(self) -> None:
        """The adapter created the connection, so it closes it."""
        with self.lock:
            self.db.close()

    def _row(self, row: tuple | None) -> Order | None:
        if row is None:
            return None
        items = tuple((name, count) for name, count in json.loads(row[2]))
        return Order(row[0], row[1], items)

    def get(self, order_id: str) -> Order | None:
        with self.lock:
            cursor = self.db.execute(
                "SELECT order_id, customer, items FROM orders WHERE order_id = ?",
                (order_id,),
            )
            return self._row(cursor.fetchone())

    def get_by_key(self, idempotency_key: str) -> Order | None:
        with self.lock:
            return self._by_key(idempotency_key)

    def _by_key(self, idempotency_key: str) -> Order | None:
        cursor = self.db.execute(
            "SELECT order_id, customer, items FROM orders WHERE idempotency_key = ?",
            (idempotency_key,),
        )
        return self._row(cursor.fetchone())

    def add(self, order: Order, idempotency_key: str) -> Order:
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?)",
                (
                    order.order_id,
                    order.customer,
                    json.dumps(order.items),
                    idempotency_key,
                ),
            )
            stored = self._by_key(idempotency_key)
        assert stored is not None
        return stored
