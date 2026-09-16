#!/usr/bin/env python3
"""Batch-check Just formatting using the installed native parser; never run recipes.

Python 3.10+. Exit 0: all discovered files pass; 1: native check fails;
2: invalid input, no matching files, missing tool, I/O error, or timeout.
No source is rewritten and no dependency is installed.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

EXCLUDED = {".git", "node_modules", ".venv", "venv", "target", ".build"}


def is_justfile(path: Path) -> bool:
    return path.name.casefold() in {"justfile", ".justfile"} or path.suffix == ".just"


def discover(inputs: Iterable[Path]) -> list[Path]:
    found: set[Path] = set()
    for value in inputs:
        if not value.exists():
            raise ValueError(f"path does not exist: {value}")
        if value.is_file():
            if not is_justfile(value):
                raise ValueError(f"not a Just source file: {value}")
            found.add(value.absolute())
        elif value.is_dir():
            # Do not follow directory symlinks or scan vendored/build directories.
            def fail(error: OSError) -> None:
                raise error

            for root, dirs, files in os.walk(value, followlinks=False, onerror=fail):
                dirs[:] = [d for d in dirs if d not in EXCLUDED]
                found.update(
                    (Path(root) / f).absolute()
                    for f in files
                    if is_justfile(Path(f)) and not (Path(root) / f).is_symlink()
                )
        else:
            raise ValueError(f"not a regular file or directory: {value}")
    return sorted(found)


def validate(
    path: Path, executable: str = "just", timeout: float = 30
) -> subprocess.CompletedProcess[str]:
    # Keep the input path intact: no shell interpolation and no whitespace splitting.
    return subprocess.run(
        [executable, "--fmt", "--check", "--justfile", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path.cwd()])
    parser.add_argument("--just", default="just", help="installed Just executable")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    if not 0 < args.timeout < float("inf"):
        parser.error("--timeout must be finite and greater than zero")
    try:
        paths = discover(args.paths)
        if not paths:
            raise ValueError("no Just sources found")
        failed = False
        for path in paths:
            result = validate(path, args.just, args.timeout)
            if result.returncode:
                failed = True
                print(
                    f"{path}: native Just check returned {result.returncode}",
                    file=sys.stderr,
                )
                print(result.stderr or result.stdout, file=sys.stderr, end="")
            else:
                print(f"PASS {path}")
        return int(failed)
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"cannot check Just sources: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
