"""Cart storage. Production uses Redis; tests use FakeRedis with the same calls."""

import json


class FakeRedis:
    """The subset of the redis-py client the cart code uses."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value


def read_cart(client, user_id: str) -> list[str]:
    raw = client.get(f"cart:{user_id}")
    return json.loads(raw) if raw else []


def write_cart(client, user_id: str, items: list[str]) -> None:
    client.set(f"cart:{user_id}", json.dumps(items))
