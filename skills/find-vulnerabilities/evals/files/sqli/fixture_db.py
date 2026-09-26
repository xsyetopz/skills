import sqlite3


def make_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE docs (id INTEGER PRIMARY KEY, title TEXT, public INTEGER)")
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT)")
    db.executemany("INSERT INTO docs VALUES (?, ?, ?)", [
        (1, "Quarterly report", 1), (2, "Holiday plan", 1), (3, "Board minutes (internal)", 0),
        (4, "100% uptime review", 1), (5, "O'Brien onboarding", 1),
    ])
    db.execute("INSERT INTO users VALUES (1, 'admin@example.invalid', 'pbkdf2$fixture$hash')")
    return db
