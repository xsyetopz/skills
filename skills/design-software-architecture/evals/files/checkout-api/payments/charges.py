"""Charge creation. The HTTP layer calls create_charge once per POST /charges."""

import sqlite3
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS charges (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=10)
    conn.executescript(SCHEMA)
    return conn


def create_charge(conn: sqlite3.Connection, customer_id: str, amount_cents: int) -> str:
    """Charge the customer and return the new charge ID."""
    if amount_cents <= 0:
        raise ValueError("amount_cents must be positive")
    charge_id = "ch_" + uuid.uuid4().hex[:12]
    with conn:
        conn.execute(
            "INSERT INTO charges (id, customer_id, amount_cents) VALUES (?, ?, ?)",
            (charge_id, customer_id, amount_cents),
        )
    return charge_id
