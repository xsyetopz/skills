#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown-it-py==4.2.0"]
# ///
"""Validate version strings against Semantic Versioning 2.0.0.

Usage:
    uv run audit_semver.py <version> [<version> ...] [--json]
    uv run audit_semver.py --from-tags          (read tags from git)
    uv run audit_semver.py --from-changelog CHANGELOG.md  (extract from changelog)

Spec: https://semver.org/
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Literal, TypedDict

from changelog_markdown import release_header, sections

SEMVER_SPEC = "https://semver.org/"

# Full semver regex from semver.org (numbered capture groups)
# cg1=major, cg2=minor, cg3=patch, cg4=prerelease, cg5=buildmetadata
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
    re.ASCII,
)

# "v" prefix is conventional but NOT part of semver
V_PREFIX_RE = re.compile(r"^v(.+)$")


class ValidVersion(TypedDict):
    version: str
    valid: Literal[True]
    major: str
    minor: str
    patch: str
    prerelease: str | None
    buildmetadata: str | None
    notes: list[str]
    warnings: list[str]
    spec: str


class InvalidVersion(TypedDict):
    version: str
    valid: Literal[False]
    error: str
    spec: str


def validate(
    version: str, *, allow_tag_prefix: bool = False
) -> ValidVersion | InvalidVersion:
    """Validate a single version string. Returns a result dict."""
    original = version
    notes: list[str] = []

    # A leading "v" is a Git-tag convention, not part of SemVer itself.
    m = V_PREFIX_RE.match(version)
    if m and allow_tag_prefix:
        notes.append("Accepted 'v' as a Git-tag wrapper; it is not part of SemVer")
        version = m.group(1)

    m = SEMVER_RE.fullmatch(version)
    if not m:
        return {
            "version": original,
            "valid": False,
            "error": f"'{original}' does not match SemVer 2.0.0 format",
            "spec": SEMVER_SPEC,
        }

    major = m.group(1)
    minor = m.group(2)
    patch = m.group(3)
    prerelease = m.group(4)
    build = m.group(5)

    result: ValidVersion = {
        "version": original,
        "valid": True,
        "major": major,
        "minor": minor,
        "patch": patch,
        "prerelease": prerelease,
        "buildmetadata": build,
        "notes": notes,
        "warnings": [],
        "spec": SEMVER_SPEC,
    }

    # Additional checks from the spec
    if major == "0":
        result["warnings"].append(
            "Major version 0: API is unstable. Anything may change at any time."
        )
    if prerelease:
        result["warnings"].append(
            "Pre-release version: unstable, may not satisfy intended compatibility."
        )

    return result


def from_git_tags() -> list[str]:
    """Extract version-like tags from git."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=version:refname"],
            capture_output=True,
            text=True,
            check=True,
        )
        tags = result.stdout.strip().splitlines()
        # Filter to tags that look like versions
        return [t for t in tags if re.match(r"^v?\d+\.\d+", t)]
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: cannot run 'git tag'. Are you in a git repo?", file=sys.stderr)
        sys.exit(1)


def from_changelog(path: Path) -> list[str]:
    """Extract version headers from a Keep a Changelog file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    versions: list[str] = []
    for section in sections(text):
        if section.level == 2:
            version, _ = release_header(section.title)
            if version.casefold() != "unreleased":
                versions.append(version)
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate version strings against Semantic Versioning 2.0.0."
    )
    parser.add_argument(
        "versions",
        nargs="*",
        help="Version strings to validate",
    )
    parser.add_argument(
        "--from-tags",
        action="store_true",
        help="Validate all version-like git tags in the current repo",
    )
    parser.add_argument(
        "--from-changelog",
        type=Path,
        metavar="PATH",
        help="Extract and validate versions from a CHANGELOG.md",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    results = [validate(value) for value in args.versions]

    if args.from_tags:
        results.extend(
            validate(value, allow_tag_prefix=True) for value in from_git_tags()
        )
    if args.from_changelog:
        results.extend(validate(value) for value in from_changelog(args.from_changelog))

    if not results:
        parser.print_help()
        return 1

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        errors = 0
        for r in results:
            if r["valid"] is True:
                extras = ""
                if r.get("prerelease"):
                    extras += f" (pre-release: {r['prerelease']})"
                if r.get("buildmetadata"):
                    extras += f" (build: {r['buildmetadata']})"
                print(
                    f"PASS  {r['version']}  ->  {r['major']}.{r['minor']}.{r['patch']}{extras}"
                )
                for note in r.get("notes", []):
                    print(f"      NOTE: {note}")
                for w in r.get("warnings", []):
                    print(f"      ⚠ {w}")
            else:
                print(f"FAIL  {r['version']}  -  {r['error']}")
                errors += 1

        total = len(results)
        print(f"\n{total - errors}/{total} valid")
        if errors:
            print(f"Spec: {SEMVER_SPEC}")
            return 1

    return int(any(not result["valid"] for result in results))


if __name__ == "__main__":
    sys.exit(main())
