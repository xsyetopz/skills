"""SQLite ledger. Applies migrations/ in order on open."""

import sqlite3
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


class Ledger:
    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path)
        for script in sorted(MIGRATIONS.glob("*.sql")):
            self._db.executescript(script.read_text())

    def add_invoice(self, customer: str, cents: int, currency: str) -> int:
        cursor = self._db.execute(
            "INSERT INTO invoices (customer, cents, currency) VALUES (?, ?, ?)",
            (customer, cents, currency),
        )
        self._db.commit()
        return int(cursor.lastrowid or 0)

    def mark_paid(self, invoice_id: int) -> bool:
        cursor = self._db.execute(
            "UPDATE invoices SET paid = 1 WHERE id = ? AND paid = 0", (invoice_id,)
        )
        self._db.commit()
        return cursor.rowcount == 1
