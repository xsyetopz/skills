#!/usr/bin/env python3
"""Count code lines per file, without blank or comment lines, and flag long files.

Lines are counted by line_count.py (next to this script): comments, Python
docstrings, and blank lines do not count. Test files are recognized by path
and have their own limit.

Directories are listed with `git ls-files` (tracked plus untracked, not
ignored) when they are inside a Git work tree; otherwise hidden, dependency,
and build directories are skipped. Files with no known comment syntax are
skipped and counted.

Usage: file_length.py PATH... [--max-code N] [--max-test N]
                      [--test-glob GLOB] [--exclude GLOB] [--all] [--json]
Exit status: 0 every file within its limit, 1 a file over its limit,
2 missing or unreadable input.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from line_count import count_code_lines

EPILOG = """examples:
  file_length.py src tests
  file_length.py . --max-code 300 --max-test 500 --exclude 'gen/*'
  file_length.py src --all --json"""


GIT_LS_FLAGS = ["-z", "--cached", "--others", "--exclude-standard"]
SKIP_DIRS = {"node_modules", "vendor", "target", "build", "dist", "__pycache__"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "e2e"}
TEST_STEM = re.compile(r"^(tests?|conftest|test_.+|.+_tests?|.+_spec)$", re.IGNORECASE)
TEST_SUFFIX = re.compile(r"[a-z0-9](Test|Tests|Spec|IT)$")
TEST_INFIX = re.compile(r"\.(test|spec)\.[^.]+$", re.IGNORECASE)


@dataclass(frozen=True)
class FileCount:
    path: str
    kind: str
    lines: int
    limit: int

    @property
    def over(self) -> bool:
        return self.lines > self.limit


def is_test(path: Path, extra_globs: list[str]) -> bool:
    posix = path.as_posix()
    if any(fnmatch(posix, glob) for glob in extra_globs):
        return True
    if TEST_DIRS.intersection(path.parts[:-1]):
        return True
    stem = path.name.split(".")[0]
    return bool(
        TEST_STEM.match(stem)
        or TEST_SUFFIX.search(stem)
        or TEST_INFIX.search(path.name)
    )


def git_files(directory: Path) -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), "ls-files", *GIT_LS_FLAGS],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    names = result.stdout.decode("utf-8", errors="replace").split("\0")
    return [directory / name for name in names if name]


def walk_files(directory: Path) -> list[Path]:
    found = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        found.extend(Path(root) / name for name in files)
    return found


def expand(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            listed = git_files(path)
            files.extend(walk_files(path) if listed is None else listed)
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"no such file or directory: {raw}")
    return sorted({f for f in files if f.is_file()})


def measure(args: argparse.Namespace) -> tuple[list[FileCount], list[str]]:
    counts, skipped = [], []
    for path in expand(args.paths):
        posix = path.as_posix()
        if any(fnmatch(posix, glob) for glob in args.exclude):
            continue
        lines = count_code_lines(path)
        if lines is None:
            skipped.append(posix)
            continue
        test = is_test(path, args.test_glob)
        limit = args.max_test if test else args.max_code
        counts.append(FileCount(posix, "test" if test else "code", lines, limit))
    return counts, skipped


def summary(counts: list[FileCount], kind: str) -> dict[str, int]:
    group = [c for c in counts if c.kind == kind]
    return {
        "files": len(group),
        "lines": sum(c.lines for c in group),
        "over": sum(c.over for c in group),
        "max": max((c.lines for c in group), default=0),
    }


def print_text(counts: list[FileCount], skipped: list[str], show_all: bool) -> None:
    for c in sorted(counts, key=lambda c: (-c.lines, c.path)):
        if show_all or c.over:
            mark = "over" if c.over else "ok"
            print(f"{c.path}: {c.lines} lines ({c.kind}, limit {c.limit}, {mark})")
    for kind in ("code", "test"):
        s = summary(counts, kind)
        print(
            f"{kind}: {s['files']} files, {s['lines']} lines, "
            f"largest {s['max']}, {s['over']} over limit"
        )
    if skipped:
        print(f"skipped: {len(skipped)} files with no known comment syntax")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="files or directories")
    parser.add_argument(
        "--max-code",
        type=int,
        default=300,
        metavar="N",
        help="limit for code files (default: 300)",
    )
    parser.add_argument(
        "--max-test",
        type=int,
        default=500,
        metavar="N",
        help="limit for test files (default: 500)",
    )
    parser.add_argument(
        "--test-glob",
        action="append",
        default=[],
        metavar="GLOB",
        help="extra path pattern that marks a test file (repeatable)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="path pattern to leave out, such as generated code (repeatable)",
    )
    parser.add_argument("--all", action="store_true", help="list files within limits")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    if args.max_code < 1 or args.max_test < 1:
        parser.error("--max-code and --max-test must be 1 or more")
    try:
        counts, skipped = measure(args)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        report = {
            "files": [asdict(c) | {"over": c.over} for c in counts],
            "summary": {kind: summary(counts, kind) for kind in ("code", "test")},
            "skipped": skipped,
        }
        print(json.dumps(report, indent=2))
    else:
        print_text(counts, skipped, args.all)
    return 1 if any(c.over for c in counts) else 0


if __name__ == "__main__":
    raise SystemExit(main())
