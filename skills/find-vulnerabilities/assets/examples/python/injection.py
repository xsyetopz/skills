"""Injection pairs: SQL, OS command, argument, and HTML output contexts.

Each ``vulnerable_*`` function is INTENTIONALLY VULNERABLE and exists only so
the tests in ``test_injection.py`` can show the exploit condition against a
local, synthetic target. Copy the ``fixed_*`` functions, never the others.
"""

from __future__ import annotations

import html
import sqlite3
import subprocess
import sys
from urllib.parse import urlsplit

SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
INSERT INTO users (name, email) VALUES
    ('alice', 'alice@example.test'),
    ('bob', 'bob@example.test'),
    ('carol', 'carol@example.test');
"""


def make_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    return db


# --- SQL injection (CWE-89) -------------------------------------------------


def vulnerable_find_user(db: sqlite3.Connection, name: str) -> list[tuple]:
    # INTENTIONALLY VULNERABLE (CWE-89): user text becomes SQL syntax.
    query = "SELECT name, email FROM users WHERE name = '" + name + "'"
    return db.execute(query).fetchall()


def fixed_find_user(db: sqlite3.Connection, name: str) -> list[tuple]:
    query = "SELECT name, email FROM users WHERE name = ?"
    return db.execute(query, (name,)).fetchall()


# --- SQL identifiers cannot be bound: map them (CWE-89) ---------------------

SORT_COLUMNS = {"name": "name", "email": "email"}


def vulnerable_list_users(db: sqlite3.Connection, sort: str) -> list[tuple]:
    # INTENTIONALLY VULNERABLE (CWE-89): identifier spliced into SQL.
    return db.execute(f"SELECT name FROM users ORDER BY {sort}").fetchall()


def fixed_list_users(
    db: sqlite3.Connection, sort: str, descending: bool = False
) -> list[tuple]:
    column = SORT_COLUMNS.get(sort)
    if column is None:
        raise ValueError(f"unsupported sort key: {sort!r}")
    direction = "DESC" if descending else "ASC"
    return db.execute(
        f"SELECT name FROM users ORDER BY {column} {direction}"
    ).fetchall()


# --- OS command injection (CWE-78) ------------------------------------------


def vulnerable_count_lines(path: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-78): the shell parses user text.
    command = "wc -l " + path
    return subprocess.run(
        command, shell=True, capture_output=True, text=True, check=False
    ).stdout


def fixed_count_lines(path: str) -> str:
    return subprocess.run(
        ["wc", "-l", "--", path], capture_output=True, text=True, check=False
    ).stdout


# --- Argument injection (CWE-88) --------------------------------------------
# argv lists stop the shell, not the program's own option parser. The child
# here is a tiny Python program with a dangerous "--exec" option.

CHILD = """
import argparse
p = argparse.ArgumentParser()
p.add_argument("--exec", dest="run")
p.add_argument("names", nargs="*")
a = p.parse_args()
print("RAN " + a.run if a.run else "NAMES " + ",".join(a.names))
"""


def vulnerable_lookup(name: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-88): a value starting with "-" is
    # parsed as an option by the child program.
    argv = [sys.executable, "-c", CHILD, name]
    return subprocess.run(argv, capture_output=True, text=True).stdout


def fixed_lookup(name: str) -> str:
    argv = [sys.executable, "-c", CHILD, "--", name]
    return subprocess.run(argv, capture_output=True, text=True).stdout


# --- Cross-site scripting (CWE-79) ------------------------------------------


def vulnerable_greeting(name: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-79): markup from user text.
    return f"<p>Hello, {name}</p>"


def fixed_greeting(name: str) -> str:
    return f"<p>Hello, {html.escape(name)}</p>"


def vulnerable_input_value(value: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-79): quote=False leaves '"' intact,
    # so the value can close the attribute and add a new one.
    return f'<input name="q" value="{html.escape(value, quote=False)}">'


def fixed_input_value(value: str) -> str:
    return f'<input name="q" value="{html.escape(value, quote=True)}">'


SAFE_LINK_SCHEMES = {"http", "https"}


def vulnerable_profile_link(url: str) -> str:
    # INTENTIONALLY VULNERABLE (CWE-79): escaping does not neutralize a
    # javascript: URL; the browser runs it when the link is followed.
    return f'<a href="{html.escape(url)}">site</a>'


def fixed_profile_link(url: str) -> str:
    if urlsplit(url.strip()).scheme.lower() not in SAFE_LINK_SCHEMES:
        return "<span>site</span>"
    return f'<a href="{html.escape(url)}">site</a>'
