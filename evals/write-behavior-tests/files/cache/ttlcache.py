"""A small in-memory cache whose entries expire after a fixed time."""

import time


class TTLCache:
    def __init__(self, ttl: float) -> None:
        self._ttl = ttl
        self._items: dict[str, tuple[float, object]] = {}

    def set(self, key: str, value: object) -> None:
        self._items[key] = (time.monotonic(), value)

    def get(self, key: str, default: object = None) -> object:
        """The stored value, or `default` once `ttl` seconds have passed since set()."""
        entry = self._items.get(key)
        if entry is None:
            return default
        stored_at, value = entry
        if time.monotonic() - stored_at >= self._ttl:
            del self._items[key]
            return default
        return value
