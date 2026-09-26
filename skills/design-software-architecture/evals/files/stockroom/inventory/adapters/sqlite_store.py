"""SQLite storage for stock levels."""

import sqlite3


class SqliteStore:
    def __init__(self, path: str = "stock.db") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS stock (sku TEXT PRIMARY KEY, on_hand INTEGER)"
        )

    def add(self, sku: str, on_hand: int) -> None:
        with self.conn:
            self.conn.execute("INSERT INTO stock VALUES (?, ?)", (sku, on_hand))

    def load(self, sku: str) -> tuple[str, int]:
        row = self.conn.execute(
            "SELECT sku, on_hand FROM stock WHERE sku = ?", (sku,)
        ).fetchone()
        if row is None:
            raise KeyError(sku)
        return row[0], row[1]

    def save(self, sku: str, on_hand: int) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE stock SET on_hand = ? WHERE sku = ?", (on_hand, sku)
            )
