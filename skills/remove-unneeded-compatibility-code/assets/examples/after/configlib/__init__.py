"""Config loader after removing compatibility code that no supported
version or saved file needs (the "after" state)."""

import tomllib

# Settings written before 1.3 used "timeout"; saved files still contain it,
# so this alias stays until a migration rewrites them.
_LEGACY_KEYS = {"timeout": "timeout_s"}


def _read(path: str) -> dict:
    with open(path, "rb") as handle:
        return tomllib.load(handle)


def load(path: str) -> dict:
    raw = _read(path)
    return {_LEGACY_KEYS.get(key, key): value for key, value in raw.items()}
