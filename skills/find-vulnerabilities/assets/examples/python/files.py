"""File-boundary pairs: path traversal, archive extraction, and TOCTOU races.

``vulnerable_*`` functions are INTENTIONALLY VULNERABLE; tests in
``test_files.py`` exercise them only inside temporary directories.
The ``between`` hooks let a test run the attacker's step at the exact
point a real race would need to hit, so the race reproduces every time.
"""

from __future__ import annotations

import os
import stat
import tarfile
from collections.abc import Callable
from pathlib import Path


def _noop() -> None:
    return None


# --- Path traversal (CWE-22) ------------------------------------------------


def vulnerable_read(root: Path, name: str) -> bytes:
    # INTENTIONALLY VULNERABLE (CWE-22): "../x" and absolute names escape.
    return Path(os.path.join(root, name)).read_bytes()


def fixed_read(root: Path, name: str) -> bytes:
    base = root.resolve()
    target = (base / name).resolve()
    if not target.is_relative_to(base):
        raise PermissionError(f"outside {base}: {name!r}")
    return target.read_bytes()


# --- Archive extraction (CWE-22) --------------------------------------------


def vulnerable_extract(archive: Path, dest: Path) -> None:
    # INTENTIONALLY VULNERABLE (CWE-22): "fully_trusted" honors "../" names
    # and absolute links. It was the implicit default before Python 3.14.
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="fully_trusted")


def fixed_extract(archive: Path, dest: Path) -> None:
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="data")


# --- TOCTOU: check a path, then open it again (CWE-367, CWE-59) -------------


def vulnerable_read_upload(path: Path, between: Callable[[], None] = _noop) -> bytes:
    # INTENTIONALLY VULNERABLE (CWE-367): the check and the open resolve the
    # path separately; a symlink swapped in between is followed.
    if path.is_symlink() or not path.is_file():
        raise PermissionError(f"not a regular file: {path}")
    between()
    return path.read_bytes()


def fixed_read_upload(path: Path, between: Callable[[], None] = _noop) -> bytes:
    between()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise PermissionError(f"not a regular file: {path}")
        return handle.read()


def vulnerable_create_report(
    path: Path, text: str, between: Callable[[], None] = _noop
) -> None:
    # INTENTIONALLY VULNERABLE (CWE-367): exists() then open("w") follows a
    # symlink planted in between and truncates its target.
    if path.exists():
        raise FileExistsError(path)
    between()
    path.write_text(text)


def fixed_create_report(
    path: Path, text: str, between: Callable[[], None] = _noop
) -> None:
    between()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(text)
