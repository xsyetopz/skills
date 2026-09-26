from typing import Protocol


class Doc:
    id: str
    title: str


class Store(Protocol):
    def find(self, query: str) -> list[Doc]: ...
