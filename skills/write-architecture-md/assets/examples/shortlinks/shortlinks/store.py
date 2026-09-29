"""SQLite persistence for links. The only module that touches sqlite3."""

import sqlite3

from shortlinks import codes

SCHEMA = "CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY, url TEXT)"


class LinkStore:
    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute(SCHEMA)

    def add(self, url: str) -> str:
        with self._db:
            cursor = self._db.execute("INSERT INTO links (url) VALUES (?)", (url,))
        assert cursor.lastrowid is not None
        return codes.encode(cursor.lastrowid)

    def resolve(self, code: str) -> str | None:
        try:
            row_id = codes.decode(code)
        except ValueError:
            return None
        row = self._db.execute(
            "SELECT url FROM links WHERE id = ?", (row_id,)
        ).fetchone()
        return row[0] if row else None
