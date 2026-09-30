#!/usr/bin/env python3
"""Report file- and directory-naming smells in a source tree.

Findings, one per file or directory:
  prefix-group      several names in one directory share a leading word
                    sequence, so the prefix stands in for a directory
  numbered-sibling  a name repeats a sibling with a number (file1, file2,
                    handler_v2) or marks a leftover copy (parser_old, x.bak)
  generic-name      a dumping-ground name (utils, helpers, common, types)
  stutter           a file name repeats its directory (http/http_server.go)
  crowded-dir       more than --max-files direct non-test files
  deep-path         a file more than --max-depth directories below its root

Names are split into lowercase words on -, _, ., spaces, and camelCase
boundaries, after Go build suffixes such as _linux or _amd64 are removed.
Test files are skipped unless --include-tests is given. Directories are listed
with `git ls-files` (tracked plus untracked, not ignored) when they are inside
a Git work tree; otherwise hidden, dependency, and build directories are
skipped.

Usage: layout_smells.py PATH... [--min-group N] [--max-files N]
                        [--max-depth N] [--exclude GLOB] [--include-tests]
                        [--json]
Exit status: 0 no findings, 1 findings, 2 missing path or bad option value.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from fnmatch import fnmatch
from pathlib import Path

EPILOG = """examples:
  layout_smells.py src
  layout_smells.py . --min-group 4 --max-files 30 --max-depth 6
  layout_smells.py src --exclude 'gen/*' --json

exit status: 0 no findings, 1 findings, 2 missing path or bad option value"""

KINDS = (
    "prefix-group",
    "numbered-sibling",
    "generic-name",
    "stutter",
    "crowded-dir",
    "deep-path",
)
GIT_LS_FLAGS = ["-z", "--cached", "--others", "--exclude-standard"]
SKIP_DIRS = {"node_modules", "vendor", "target", "build", "dist", "__pycache__"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "e2e"}
TEST_STEM = re.compile(r"^(tests?|conftest|test_.+|.+_tests?|.+_spec)$", re.IGNORECASE)
TEST_SUFFIX = re.compile(r"[a-z0-9](Test|Tests|Spec|IT)$")
TEST_INFIX = re.compile(r"\.(test|spec)\.[^.]+$", re.IGNORECASE)

GOOS = "linux|darwin|windows|freebsd|netbsd|openbsd|android|ios|js|wasip1"
GOARCH = "amd64|arm64|386|arm|wasm|riscv64"
GO_SUFFIX = re.compile(rf"(?<=.)_(?:(?:{GOOS})(?:_(?:{GOARCH}))?|{GOARCH})$")
SEPARATOR = re.compile(r"[-_.\s]+")
WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")
LEFTOVER = {"old", "new", "copy", "bak", "orig", "final"}
BACKUP_SUFFIXES = (".orig", ".bak")
GENERIC = {
    "util",
    "utils",
    "utility",
    "utilities",
    "helper",
    "helpers",
    "common",
    "misc",
    "stuff",
    "shared",
    "types",
    "constants",
    "models",
    "enums",
    "interfaces",
    "globals",
    "functions",
}


@dataclass(frozen=True, order=True)
class Finding:
    kind: str
    path: str
    detail: str


@dataclass(frozen=True)
class Entry:
    root: Path
    path: Path
    stem: str
    words: tuple[str, ...]


def is_test(path: Path) -> bool:
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


def expand(paths: list[str]) -> list[tuple[Path, Path]]:
    """Return (root, file) pairs; a file argument is its own directory's root."""
    pairs: dict[Path, Path] = {}
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            listed = git_files(path)
            for found in walk_files(path) if listed is None else listed:
                if found.is_file():
                    pairs.setdefault(found, path)
        elif path.is_file():
            pairs.setdefault(path, path.parent)
        else:
            raise FileNotFoundError(f"no such file or directory: {raw}")
    return sorted((root, file) for file, root in pairs.items())


def words(text: str) -> tuple[str, ...]:
    return tuple(
        word.lower() for part in SEPARATOR.split(text) for word in WORD.findall(part)
    )


def stem_of(path: Path) -> str:
    stem = path.name.split(".")[0]
    return GO_SUFFIX.sub("", stem) if path.suffix == ".go" else stem


def dir_name(directory: Path) -> str:
    return directory.name or Path(os.path.abspath(directory)).name


def prefix_groups(
    directory: str, entries: list[Entry], min_group: int
) -> list[Finding]:
    """Report each longest word prefix shared by min_group or more distinct stems.

    A prefix is dropped when a one-word-longer prefix names the same stems,
    so nested groups (cart, then cart-item) are both kept.
    """
    stems = {e.stem: e.words for e in entries}
    groups: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for stem, stem_words in stems.items():
        for size in range(1, len(stem_words) + 1):
            groups[stem_words[:size]].add(stem)
    findings = []
    for prefix, members in groups.items():
        if len(members) < max(min_group, 2):
            continue
        size = len(prefix)
        nexts = {stems[s][size] for s in members if len(stems[s]) > size}
        if any(groups[(*prefix, word)] == members for word in nexts):
            continue
        names = ", ".join(sorted(members))
        detail = f'prefix "{"-".join(prefix)}" shared by {len(members)} names: {names}'
        findings.append(Finding("prefix-group", directory, detail))
    return findings


def leftover(entry: Entry) -> str | None:
    name, found = entry.path.name, entry.words
    if name.endswith("~") or name.lower().endswith(BACKUP_SUFFIXES):
        return "backup suffix marks a leftover copy"
    if found[:2] == ("copy", "of"):
        return '"copy of" marks a leftover copy'
    last = len(found) - 1
    if found and found[-1].isdigit():
        last -= 1
    if last >= 1 and found[last] in LEFTOVER:
        return f'"{found[last]}" marks a leftover version'
    return None


def split_number(found: tuple[str, ...]) -> tuple[tuple[str, ...], str] | None:
    if len(found) < 2 or not found[-1].isdigit():
        return None
    base = found[:-1]
    if base[-1] == "v" and len(base) > 1:
        base = base[:-1]
    return base, found[-1]


def numbered_siblings(entries: list[Entry]) -> list[Finding]:
    stems = {e.stem: e.words for e in entries}
    plain = {found: stem for stem, found in stems.items()}
    numbers: dict[tuple[str, ...], dict[str, str]] = defaultdict(dict)
    for stem, found in stems.items():
        split = split_number(found)
        if split:
            numbers[split[0]][split[1]] = stem
    findings = []
    for entry in entries:
        detail = leftover(entry)
        split = split_number(entry.words)
        if detail is None and split:
            base, number = split
            others = [s for n, s in numbers[base].items() if n != number]
            other = plain.get(base) or min(others, default=None)
            if other:
                detail = f'"{entry.stem}" repeats "{other}" with a number'
        if detail:
            findings.append(Finding("numbered-sibling", entry.path.as_posix(), detail))
    return findings


def is_generic(found: tuple[str, ...]) -> bool:
    return bool(found) and all(word in GENERIC for word in found)


def name_findings(directory: Path, entries: list[Entry]) -> list[Finding]:
    findings = []
    parent = words(dir_name(directory))
    for entry in entries:
        path = entry.path.as_posix()
        if is_generic(entry.words):
            detail = f'"{entry.stem}" says nothing about what the file holds'
            findings.append(Finding("generic-name", path, detail))
        size = len(parent)
        if parent and len(entry.words) > size and entry.words[:size] == parent:
            detail = f'"{entry.stem}" repeats its directory "{dir_name(directory)}"'
            findings.append(Finding("stutter", path, detail))
    return findings


def layout_findings(entries: list[Entry], args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    by_dir: dict[Path, list[Entry]] = defaultdict(list)
    generic_dirs: set[Path] = set()
    for entry in entries:
        by_dir[entry.path.parent].append(entry)
        relative = entry.path.relative_to(entry.root)
        for depth in range(1, len(relative.parts)):
            directory = entry.root.joinpath(*relative.parts[:depth])
            if is_generic(words(directory.name)):
                generic_dirs.add(directory)
        depth = len(relative.parts) - 1
        if args.max_depth is not None and depth > args.max_depth:
            detail = f"{depth} directories deep (limit {args.max_depth})"
            findings.append(Finding("deep-path", entry.path.as_posix(), detail))
    for directory in generic_dirs:
        detail = f'directory "{directory.name}" says nothing about what it holds'
        findings.append(Finding("generic-name", directory.as_posix(), detail))
    for directory, group in by_dir.items():
        named = [e for e in group if e.words]
        findings += prefix_groups(directory.as_posix(), named, args.min_group)
        findings += numbered_siblings(named)
        findings += name_findings(directory, named)
        code = sum(not is_test(e.path) for e in group)
        if args.max_files is not None and code > args.max_files:
            detail = f"{code} files (limit {args.max_files})"
            findings.append(Finding("crowded-dir", directory.as_posix(), detail))
    return sorted(findings)


def collect(args: argparse.Namespace) -> list[Entry]:
    entries = []
    for root, path in expand(args.paths):
        if any(fnmatch(path.as_posix(), glob) for glob in args.exclude):
            continue
        if not args.include_tests and is_test(path):
            continue
        stem = stem_of(path)
        entries.append(Entry(root, path, stem, words(stem)))
    return entries


def summary(findings: list[Finding]) -> dict[str, int]:
    return {kind: sum(f.kind == kind for f in findings) for kind in KINDS}


def print_text(findings: list[Finding]) -> None:
    for f in findings:
        print(f"{f.kind} {f.path}: {f.detail}")
    counts = ", ".join(f"{k} {n}" for k, n in summary(findings).items() if n)
    print(f"findings: {len(findings)}" + (f" ({counts})" if counts else ""))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="files or directories")
    parser.add_argument(
        "--min-group",
        type=int,
        default=3,
        metavar="N",
        help="distinct names that make a prefix group (default: 3)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        metavar="N",
        help="report directories with more than N direct non-test files",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        metavar="N",
        help="report files more than N directories below their PATH",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="path pattern to leave out, such as generated code (repeatable)",
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="analyze test files too"
    )
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    limits = (args.min_group, args.max_files, args.max_depth)
    if any(n is not None and n < 1 for n in limits):
        parser.error("--min-group, --max-files, and --max-depth must be 1 or more")
    try:
        findings = layout_findings(collect(args), args)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        report = {
            "findings": [asdict(f) for f in findings],
            "summary": summary(findings),
        }
        print(json.dumps(report, indent=2))
    else:
        print_text(findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
