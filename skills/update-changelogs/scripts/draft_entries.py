#!/usr/bin/env python3
"""Draft Keep a Changelog entries from Conventional Commits in a Git range.

Reads `git log --no-merges RANGE` in the current repository and groups
commits whose subjects follow Conventional Commits 1.0.0
(`type(scope)!: summary`):

  feat               -> Added
  fix                -> Fixed
  perf, revert       -> Changed
  `!` or a `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer
                     -> Changed, marked breaking
  docs, test, ci, build, chore, style, refactor -> omitted (not user-facing)
  anything else      -> listed under "Unclassified" for a human to sort

It prints a Markdown draft and a suggested SemVer increment (major if any
breaking change, else minor if any feat, else patch if any fix/perf/revert,
else none). The draft is input for editing, not a finished changelog:
rewrite entries as user-visible consequences and check each against its
commit.

Usage: draft_entries.py RANGE [--version X.Y.Z --date YYYY-MM-DD] [--json]
Exit status: 0 success, 2 git error or invalid range.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass

SUBJECT = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?: (?P<summary>.+)$"
)
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: ", re.MULTILINE)
CATEGORY = {"feat": "Added", "fix": "Fixed", "perf": "Changed", "revert": "Changed"}
OMITTED = {"docs", "test", "ci", "build", "chore", "style", "refactor"}
ORDER = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
EPILOG = """\
Exit status:
  0  draft printed (possibly empty)
  2  git log failed: not a repository or an unknown revision range

Output: a Markdown draft ending in "<!-- suggested SemVer increment: X -->".
--json prints {"heading", "bump", "categories": {NAME: [entries]},
"unclassified": [entries]}; only non-empty categories are listed.
Read-only: nothing is written; paste the draft into CHANGELOG.md by hand.

Examples:
  python3 scripts/draft_entries.py v1.2.0..HEAD
  python3 scripts/draft_entries.py v1.2.0..HEAD --version 1.3.0 --date 2026-09-26
  python3 scripts/draft_entries.py v1.2.0..HEAD --json | jq -r .bump
"""


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


@dataclass
class Draft:
    categories: dict[str, list[str]]
    unclassified: list[str]
    bump: str


def read_commits(revision_range: str) -> list[Commit]:
    output = subprocess.run(
        [
            "git",
            "log",
            "--no-merges",
            "--reverse",
            "--format=%h%x00%s%x00%b%x1e",
            revision_range,
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits = []
    for record in output.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        sha, subject, body = [*record.split("\x00"), "", ""][:3]
        commits.append(Commit(sha, subject, body))
    return commits


def build_draft(commits: list[Commit]) -> Draft:
    categories: dict[str, list[str]] = {name: [] for name in ORDER}
    unclassified: list[str] = []
    has_breaking = has_feat = has_patch = False
    for commit in commits:
        match = SUBJECT.match(commit.subject)
        if not match:
            unclassified.append(f"{commit.subject} ({commit.sha})")
            continue
        kind = match.group("type")
        breaking = bool(match.group("bang")) or bool(
            BREAKING_FOOTER.search(commit.body)
        )
        scope = match.group("scope")
        summary = match.group("summary")
        text = f"{scope}: {summary}" if scope else summary
        if breaking:
            has_breaking = True
            categories["Changed"].append(f"**Breaking:** {text} ({commit.sha})")
        elif kind in CATEGORY:
            has_feat = has_feat or kind == "feat"
            has_patch = has_patch or kind != "feat"
            categories[CATEGORY[kind]].append(f"{text} ({commit.sha})")
        elif kind not in OMITTED:
            unclassified.append(f"{commit.subject} ({commit.sha})")
    if has_breaking:
        bump = "major"
    elif has_feat:
        bump = "minor"
    elif has_patch:
        bump = "patch"
    else:
        bump = "none"
    return Draft(categories, unclassified, bump)


def render(draft: Draft, heading: str) -> str:
    lines = [f"## {heading}", ""]
    for name in ORDER:
        entries = draft.categories[name]
        if not entries:
            continue
        lines += [f"### {name}", ""]
        lines += [f"- {entry}" for entry in entries]
        lines.append("")
    if draft.unclassified:
        lines += ["### Unclassified (sort by hand)", ""]
        lines += [f"- {entry}" for entry in draft.unclassified]
        lines.append("")
    lines.append(f"<!-- suggested SemVer increment: {draft.bump} -->")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("range", help="for example v1.2.0..HEAD")
    parser.add_argument("--version", help="release version for the heading")
    parser.add_argument("--date", help="release date (YYYY-MM-DD) with --version")
    parser.add_argument("--json", action="store_true", help="print a JSON draft")
    args = parser.parse_args(argv)
    try:
        commits = read_commits(args.range)
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", "") or str(error)
        print(
            f"error: git log failed: {detail.strip()}; run inside the repository "
            "with a range such as v1.2.0..HEAD",
            file=sys.stderr,
        )
        return 2
    heading = "[Unreleased]"
    if args.version:
        heading = f"[{args.version}] - {args.date or 'YYYY-MM-DD'}"
    if args.json:
        draft = build_draft(commits)
        document = {
            "heading": heading,
            "bump": draft.bump,
            "categories": {k: v for k, v in draft.categories.items() if v},
            "unclassified": draft.unclassified,
        }
        print(json.dumps(document, indent=2))
        return 0
    print(render(build_draft(commits), heading))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
