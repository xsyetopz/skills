#!/usr/bin/env python3
"""Count competing terms for one concept across source identifiers and text.

Identifiers are split on snake_case, kebab-case, camelCase, and PascalCase
boundaries, so `userRepo`, `user_repo`, and `UserRepo` all count as the word
`repo`. Matching is case-insensitive and whole-word.

Usage:
  term_report.py --group repository=repository,repo,store PATH...
                 [--group ...] [--ext .py --ext .ts ...] [--allow-mixed]
                 [--json]

Each --group names the canonical term first, then its competitors. The
report lists files per term. Exit status: 0 when every group uses only its
canonical term (or --allow-mixed), 1 when a competing term appears, 2 on bad
input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_EXTENSIONS = (
    ".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".kt",
    ".lua", ".md", ".py", ".rb", ".rs", ".scala", ".swift", ".ts", ".tsx",
)  # fmt: skip
SKIP_DIRS = {".git", "node_modules", "target", "bin", "obj", ".build", "dist"}
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*")
CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+")
EPILOG = """\
Exit status:
  0  every group uses only its canonical term (or --allow-mixed)
  1  a competing term appears
  2  bad input: a malformed --group or a PATH that does not exist

Output: per group, "CONCEPT: canonical 'TERM'" and one line per term with
its total and file count; files are listed under competing terms that
appear. --json prints {"groups": [{concept, canonical, terms: [{term,
total, competing, files: {PATH: N}}]}], "mixed": bool}.

Examples:
  python3 scripts/term_report.py --group repository=repository,repo,store src
  python3 scripts/term_report.py --group user=user,account,member \\
    --ext .ts --ext .tsx web/src --json
"""


def words(text: str) -> list[str]:
    result: list[str] = []
    for token in TOKEN.findall(text):
        result.extend(part.lower() for part in CAMEL.findall(token))
    return result


def parse_group(raw: str) -> tuple[str, list[str]]:
    concept, _, terms = raw.partition("=")
    names = [t.strip().lower() for t in terms.split(",") if t.strip()]
    if not concept or len(names) < 2:
        raise ValueError(f"--group needs concept=canonical,alternative: {raw}")
    return concept, names


def source_files(paths: list[str], extensions: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
            continue
        if not path.is_dir():
            raise FileNotFoundError(f"{raw} does not exist; pass files or directories")
        for candidate in sorted(path.rglob("*")):
            if SKIP_DIRS.intersection(candidate.parts):
                continue
            if candidate.is_file() and candidate.suffix in extensions:
                files.append(candidate)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="source files or directories")
    parser.add_argument(
        "--group",
        action="append",
        required=True,
        metavar="CONCEPT=CANONICAL,ALT[,...]",
        help="concept, canonical term first; repeatable",
    )
    parser.add_argument(
        "--ext", action="append", help="file extension to scan; repeatable"
    )
    parser.add_argument(
        "--allow-mixed", action="store_true", help="report but exit 0 on mixed terms"
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    extensions = tuple(args.ext) if args.ext else DEFAULT_EXTENSIONS
    try:
        groups = [parse_group(raw) for raw in args.group]
        files = source_files(args.paths, extensions)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        seen = words(text)
        for _, terms in groups:
            for term in terms:
                occurrences = seen.count(term)
                if occurrences:
                    counts[term][str(path)] += occurrences

    if args.json:
        report = [
            {
                "concept": concept,
                "canonical": terms[0],
                "terms": [
                    {
                        "term": term,
                        "total": sum(counts[term].values()),
                        "competing": term != terms[0],
                        "files": dict(sorted(counts[term].items())),
                    }
                    for term in terms
                ],
            }
            for concept, terms in groups
        ]
        mixed = any(
            entry["competing"] and entry["total"]
            for group in report
            for entry in group["terms"]
        )
        print(json.dumps({"groups": report, "mixed": mixed}, indent=2))
        return 1 if mixed and not args.allow_mixed else 0
    drift = False
    for concept, terms in groups:
        canonical, competitors = terms[0], terms[1:]
        print(f"{concept}: canonical '{canonical}'")
        for term in terms:
            total = sum(counts[term].values())
            label = "canonical" if term == canonical else "competing"
            print(f"  {term:<16} {total:>6} ({label}, {len(counts[term])} files)")
            if term in competitors and total:
                drift = True
                for path, n in sorted(counts[term].items()):
                    print(f"    {path}: {n}")
    return 1 if drift and not args.allow_mixed else 0


if __name__ == "__main__":
    raise SystemExit(main())
