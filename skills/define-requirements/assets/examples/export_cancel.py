"""Reference implementation of export-cancellation-spec.md.

A job writes to a temporary file, then publishes by atomic rename. One
lock arbitrates cancel against publication: the state change to
"publishing" is the linearization point.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Callable


class ValidationError(ValueError):
    """Export content broke a validation rule; the message names it."""


class ExportJob:
    def __init__(
        self,
        destination: Path,
        content: bytes,
        before_publish: Callable[[], None] = lambda: None,
    ) -> None:
        self.destination = destination
        self.temporary = destination.with_name(destination.name + ".tmp")
        self.content = content
        self.before_publish = before_publish
        self.state = "writing"
        self.error: str | None = None
        self._lock = threading.Lock()

    def run(self) -> None:
        self.temporary.write_bytes(self.content)
        try:
            validate(self.content)
        except ValidationError as error:
            self._remove_temporary()
            with self._lock:
                self.state = "failed"
                self.error = str(error)
            return
        self.before_publish()
        with self._lock:
            if self.state == "cancelled":
                return
            self.state = "publishing"
        os.replace(self.temporary, self.destination)
        with self._lock:
            self.state = "published"

    def cancel(self) -> str:
        with self._lock:
            if self.state == "writing":
                self.state = "cancelled"
                self._remove_temporary()
                return "cancelled"
            if self.state == "publishing":
                return "publication started"
            return self.state

    def _remove_temporary(self) -> None:
        self.temporary.unlink(missing_ok=True)


def validate(content: bytes) -> None:
    if not content.startswith(b"EXPORT\n"):
        raise ValidationError("rule V1: content must start with EXPORT header")
