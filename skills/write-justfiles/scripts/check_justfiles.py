#!/usr/bin/env python3
"""Check Just formatting and reject deprecated environment functions."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

DEPRECATED_ENV = re.compile(r"\b(env_var|env_var_or_default)\s*\(")


def is_justfile(path: Path) -> bool:
    return path.name.casefold() == "justfile" or path.suffix == ".just"


def discover(inputs: Iterable[Path]) -> list[Path]:
    found: set[Path] = set()
    for value in inputs:
        if value.is_file() and is_justfile(value):
            found.add(value)
        elif value.is_dir():
            found.update(
                path
                for path in value.rglob("*")
                if path.is_file()
                and is_justfile(path)
                and ".git" not in path.parts
                and "node_modules" not in path.parts
            )
    return sorted(found)


def validate(path: Path) -> list[str]:
    errors = [
        f"{path}:{line}: deprecated {match.group(1)}(); use env()"
        for line, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if (match := DEPRECATED_ENV.search(text))
    ]
    result = subprocess.run(
        ["just", "--fmt", "--check", "--justfile", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        errors.append(f"{path}: just --fmt --check failed: {detail}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path.cwd()])
    args = parser.parse_args()
    paths = discover(args.paths)
    if not paths:
        print("no justfiles found", file=sys.stderr)
        return 1
    try:
        errors = [error for path in paths for error in validate(path)]
    except (OSError, UnicodeError) as error:
        print(f"cannot validate justfiles: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
