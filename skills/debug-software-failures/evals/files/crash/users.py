"""User lookup backed by a JSON file."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str


class UserStore:
    def __init__(self, path: Path) -> None:
        self._users = {row["id"]: User(**row) for row in json.loads(path.read_text())}

    def find_user(self, user_id: int) -> User:
        """Return the user with `user_id`."""
        return self._users.get(user_id)
