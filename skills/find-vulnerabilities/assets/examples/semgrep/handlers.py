"""Taint-rule target. ``search_vulnerable`` is INTENTIONALLY VULNERABLE."""

from __future__ import annotations

import sqlite3
from typing import Protocol


class Args(Protocol):
    def get(self, key: str) -> str: ...


class Request(Protocol):
    args: Args


def search_vulnerable(request: Request, db: sqlite3.Connection) -> list:
    name = request.args.get("name")
    query = "SELECT id FROM users WHERE name = '" + name + "'"
    return db.execute(query).fetchall()  # CWE-89: flagged


def search_fixed(request: Request, db: sqlite3.Connection) -> list:
    name = request.args.get("name")
    query = "SELECT id FROM users WHERE name = ?"
    return db.execute(query, (name,)).fetchall()  # not flagged


def page_sanitized(request: Request, db: sqlite3.Connection) -> list:
    limit = int(request.args.get("limit"))
    return db.execute(f"SELECT id FROM users LIMIT {limit}").fetchall()
