"""LSP base-protocol framing and position units (LSP 3.17).

Content-Length counts BYTES of the UTF-8 body. One read can hold several
messages or part of one, so the reader keeps a buffer. Positions count
UTF-16 code units unless the peers negotiated another encoding.
"""

from __future__ import annotations

import json


def encode(message: dict) -> bytes:
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


class Reader:
    """Feed arbitrary chunks; collect complete messages."""

    def __init__(self) -> None:
        self.buffer = b""

    def feed(self, chunk: bytes) -> list[dict]:
        self.buffer += chunk
        messages = []
        while True:
            end = self.buffer.find(b"\r\n\r\n")
            if end < 0:
                return messages
            headers = self.buffer[:end].decode("ascii").split("\r\n")
            length = next(
                int(h.split(":", 1)[1])
                for h in headers
                if h.lower().startswith("content-length:")
            )
            start = end + 4
            if len(self.buffer) < start + length:
                return messages
            messages.append(json.loads(self.buffer[start : start + length]))
            self.buffer = self.buffer[start + length :]


def character_offset(line: str, column_chars: int, encoding: str = "utf-16") -> int:
    """LSP `character` for the Python str index column_chars in line."""
    prefix = line[:column_chars]
    if encoding == "utf-16":
        return len(prefix.encode("utf-16-le")) // 2
    if encoding == "utf-8":
        return len(prefix.encode("utf-8"))
    if encoding == "utf-32":
        return len(prefix)
    raise ValueError(encoding)
