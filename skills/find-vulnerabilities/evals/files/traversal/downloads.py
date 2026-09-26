"""Serve files that users uploaded into the uploads directory."""

import os


def read_upload(base_dir: str, name: str) -> bytes:
    """Contents of the uploaded file `name` (may include subdirectories) under base_dir."""
    path = os.path.join(base_dir, name)
    with open(path, "rb") as handle:
        return handle.read()
