#!/usr/bin/env python3
"""Find logical (change) coupling: pairs of files that change in the same commits.

This reimplements the `coupling` analysis of Adam Tornhill's code-maat. For
each pair of files, degree = shared revisions / average of the two files'
revision counts, as a whole-number percentage (rounded down); average-revs
is that average rounded up. A pair is
reported when that average is at least --min-revs, they share at least
--min-shared revisions, and the degree is at least --min-coupling.

History comes from `git log --no-merges --no-renames --name-only`. Commits
that touch more than --max-changeset files are ignored, because large
reformat or rename commits couple everything. Test files are dropped before
counting unless --include-tests is given: a test that changes with its code
is expected coupling, not a smell. The cross column marks pairs in different
directories, which can point to a layer-by-type layout or Shotgun Surgery.

Usage: change_coupling.py [--repo DIR] [--since DATE] [--min-revs N]
                          [--min-shared N] [--min-coupling PCT]
                          [--max-changeset N] [--include-tests] [--json]
                          [--limit N]
Exit status: 0 no pair meets the thresholds, 1 at least one pair reported,
2 not a Git repository, git missing, or bad option values.
"""

from __future__ import annotations

import argparse
import json
import math
import posixpath
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import PurePosixPath

EPILOG = """examples:
  change_coupling.py
  change_coupling.py --repo ../app --since 2025-01-01 --limit 20
  change_coupling.py --min-revs 10 --min-coupling 50 --json

method: code-maat's `coupling` analysis (degree = shared revisions / average
revisions of the two files). Test files are dropped by default; pass
--include-tests to count them.

exit status: 0 no pair meets the thresholds, 1 at least one pair reported,
2 not a Git repository, git missing, or bad option values."""

COMMIT_HEADER = re.compile(r"^--[0-9a-f]{4,}$")
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "e2e"}
TEST_STEM = re.compile(r"^(tests?|conftest|test_.+|.+_tests?|.+_spec)$", re.IGNORECASE)
TEST_SUFFIX = re.compile(r"[a-z0-9](Test|Tests|Spec|IT)$")
TEST_INFIX = re.compile(r"\.(test|spec)\.[^.]+$", re.IGNORECASE)


@dataclass(frozen=True)
class Pair:
    entity: str
    coupled: str
    degree: int
    average_revs: int
    shared_revs: int
    cross_dir: bool


@dataclass
class Stats:
    commits: int = 0
    skipped_large: int = 0
    files: int = 0
    above_thresholds: int = 0


def is_test(path: str) -> bool:
    parts = PurePosixPath(path)
    if TEST_DIRS.intersection(parts.parts[:-1]):
        return True
    stem = parts.name.split(".")[0]
    return bool(
        TEST_STEM.match(stem)
        or TEST_SUFFIX.search(stem)
        or TEST_INFIX.search(parts.name)
    )


def parse_log(text: str) -> list[set[str]]:
    """Split `--pretty=format:--%h --name-only` output into per-commit file sets."""
    commits: list[set[str]] = []
    for line in text.splitlines():
        if COMMIT_HEADER.match(line):
            commits.append(set())
        elif line.strip() and commits:
            commits[-1].add(line)
    return commits


def couple(
    commits: list[set[str]],
    min_revs: int = 5,
    min_shared: int = 5,
    min_coupling: int = 30,
    max_changeset: int = 30,
    include_tests: bool = False,
    stats: Stats | None = None,
) -> list[Pair]:
    """Count revisions and shared revisions, and return pairs over the thresholds.

    The changeset size is the commit's full file count, before test files are
    dropped. Results are sorted by degree, then shared revisions, descending.
    """
    stats = stats if stats is not None else Stats()
    revs: Counter[str] = Counter()
    shared: Counter[tuple[str, str]] = Counter()
    for files in commits:
        stats.commits += 1
        if len(files) > max_changeset:
            stats.skipped_large += 1
            continue
        kept = sorted(f for f in files if include_tests or not is_test(f))
        revs.update(kept)
        shared.update(combinations(kept, 2))
    stats.files = len(revs)
    pairs = []
    for (entity, coupled), count in shared.items():
        average = (revs[entity] + revs[coupled]) / 2
        if average < min_revs or count < min_shared:
            continue
        degree = int(100 * count / average)
        if degree < min_coupling:
            continue
        cross = posixpath.dirname(entity) != posixpath.dirname(coupled)
        pairs.append(Pair(entity, coupled, degree, math.ceil(average), count, cross))
    pairs.sort(key=lambda p: (-p.degree, -p.shared_revs, p.entity, p.coupled))
    stats.above_thresholds = len(pairs)
    return pairs


def git_log(repo: str, since: str | None) -> str:
    """Return the raw log text; raise OSError when git is missing or fails."""
    command = ["git", "-C", repo, "-c", "core.quotePath=false", "log"]
    command += ["--no-merges", "--no-renames", "--name-only", "--pretty=format:--%h"]
    if since:
        command.append(f"--since={since}")
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise OSError(message or f"git log failed with status {result.returncode}")
    return result.stdout.decode("utf-8", errors="replace")


def summary(pairs: list[Pair], stats: Stats) -> dict[str, int]:
    return {
        "commits": stats.commits,
        "skipped_large_commits": stats.skipped_large,
        "files": stats.files,
        "pairs_above_thresholds": stats.above_thresholds,
        "pairs_reported": len(pairs),
        "cross_dir_pairs": sum(p.cross_dir for p in pairs),
    }


def print_text(pairs: list[Pair], stats: Stats, max_changeset: int) -> None:
    if pairs:
        print(f"{'degree%':>7} {'shared':>6} {'avg-revs':>8} {'cross':>5}  pair")
    for p in pairs:
        cross = "yes" if p.cross_dir else "no"
        print(
            f"{p.degree:>6}% {p.shared_revs:>6} {p.average_revs:>8} {cross:>5}  "
            f"{p.entity} <-> {p.coupled}"
        )
    s = summary(pairs, stats)
    print(
        f"{s['pairs_reported']} pairs reported "
        f"({s['cross_dir_pairs']} cross directories) "
        f"of {s['pairs_above_thresholds']} above thresholds; "
        f"{s['commits']} commits, {s['files']} files, "
        f"{s['skipped_large_commits']} commits over {max_changeset} files skipped"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", default=".", metavar="DIR", help="Git work tree")
    parser.add_argument(
        "--since", metavar="DATE", help="only commits after DATE (git log --since)"
    )
    parser.add_argument(
        "--min-revs",
        type=int,
        default=5,
        metavar="N",
        help="average revisions the pair needs (default: 5)",
    )
    parser.add_argument(
        "--min-shared",
        type=int,
        default=5,
        metavar="N",
        help="shared revisions a pair needs (default: 5)",
    )
    parser.add_argument(
        "--min-coupling",
        type=int,
        default=30,
        metavar="PCT",
        help="minimum degree in percent, 1..100 (default: 30)",
    )
    parser.add_argument(
        "--max-changeset",
        type=int,
        default=30,
        metavar="N",
        help="ignore commits with more files than N (default: 30)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="count test files too; by default they are dropped, because a test "
        "that changes with its code is expected coupling",
    )
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        metavar="N",
        help="report at most N pairs (default: 50)",
    )
    args = parser.parse_args(argv)
    for name in ("min_revs", "min_shared", "max_changeset", "limit"):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be 1 or more")
    if not 1 <= args.min_coupling <= 100:
        parser.error("--min-coupling must be between 1 and 100")
    try:
        text = git_log(args.repo, args.since)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    stats = Stats()
    pairs = couple(
        parse_log(text),
        args.min_revs,
        args.min_shared,
        args.min_coupling,
        args.max_changeset,
        args.include_tests,
        stats,
    )[: args.limit]
    if args.json:
        report = {
            "pairs": [asdict(p) for p in pairs],
            "summary": summary(pairs, stats),
        }
        print(json.dumps(report, indent=2))
    else:
        print_text(pairs, stats, args.max_changeset)
    return 1 if pairs else 0


if __name__ == "__main__":
    raise SystemExit(main())
