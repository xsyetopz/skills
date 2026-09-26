"""Document search used by the /search endpoint."""

import sqlite3


def search(db: sqlite3.Connection, q: str, sort: str = "title") -> list[tuple[int, str]]:
    """Public documents whose title contains `q`, ordered by `sort` (title or id)."""
    sql = f"SELECT id, title FROM docs WHERE public = 1 AND title LIKE '%{q}%' ORDER BY {sort}"
    return db.execute(sql).fetchall()
