"""Argon2id password hashing with argon2-cffi.

Run: uv run --no-project --with argon2-cffi python argon2_hash.py
Uses OWASP's first Argon2id option: m=47104 KiB (46 MiB), t=1, p=1.
"""

from __future__ import annotations

import secrets
from importlib.metadata import version

from argon2 import PasswordHasher  # pyright: ignore[reportMissingImports]
from argon2.exceptions import (  # pyright: ignore[reportMissingImports]
    VerifyMismatchError,
)

HASHER = PasswordHasher(time_cost=1, memory_cost=47104, parallelism=1)


def main() -> int:
    password = secrets.token_hex(8)
    first, second = HASHER.hash(password), HASHER.hash(password)
    print("encoded:", first.split("$")[1:4])
    assert first != second, "salt must differ"
    assert HASHER.verify(first, password)
    try:
        HASHER.verify(first, password + "x")
    except VerifyMismatchError:
        print("wrong password rejected")
    else:
        return 1
    print(
        "needs rehash at stronger params:",
        PasswordHasher(time_cost=2).check_needs_rehash(first),
    )
    print("argon2-cffi", version("argon2-cffi"), "PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
