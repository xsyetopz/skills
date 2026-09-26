"""A tiny in-process FIFO job queue."""

from collections import deque


class Queue:
    def __init__(self) -> None:
        self._jobs: deque[str] = deque()

    def put(self, job: str) -> None:
        self._jobs.append(job)

    def get(self) -> str | None:
        return self._jobs.popleft() if self._jobs else None
