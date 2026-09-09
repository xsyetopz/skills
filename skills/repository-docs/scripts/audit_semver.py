#!/usr/bin/env python3
"""Validate version strings against Semantic Versioning 2.0.0.

Usage:
    python3 audit_semver.py <version> [<version> ...] [--json]
    python3 audit_semver.py --from-tags          (read tags from git)
    python3 audit_semver.py --from-changelog CHANGELOG.md  (extract from changelog)

Spec: https://semver.org/
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SEMVER_SPEC = "https://semver.org/"

# Full semver regex from semver.org (numbered capture groups)
# cg1=major, cg2=minor, cg3=patch, cg4=prerelease, cg5=buildmetadata
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# "v" prefix is conventional but NOT part of semver
V_PREFIX_RE = re.compile(r"^v(.+)$")

# Version extractor from changelog lines
CHANGELOG_VERSION_RE = re.compile(
    r"^##\s+\[(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)\]"
)


def validate(version: str) -> dict:
    """Validate a single version string. Returns a result dict."""
    original = version
    notes: list[str] = []

    # Strip "v" prefix (convention, not spec)
    m = V_PREFIX_RE.match(version)
    if m:
        notes.append("Stripped 'v' prefix (conventional, not part of SemVer)")
        version = m.group(1)

    m = SEMVER_RE.match(version)
    if not m:
        return {
            "version": original,
            "valid": False,
            "error": f"'{original}' does not match SemVer 2.0.0 format",
            "spec": SEMVER_SPEC,
        }

    major = int(m.group(1))
    minor = int(m.group(2))
    patch = int(m.group(3))
    prerelease = m.group(4)
    build = m.group(5)

    result = {
        "version": original,
        "valid": True,
        "major": major,
        "minor": minor,
        "patch": patch,
        "prerelease": prerelease,
        "buildmetadata": build,
        "notes": notes,
        "spec": SEMVER_SPEC,
    }

    # Additional checks from the spec
    if major == 0:
        result.setdefault("warnings", []).append(
            "Major version 0: API is unstable. Anything may change at any time."
        )
    if prerelease:
        result.setdefault("warnings", []).append(
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
    for line in text.splitlines():
        m = CHANGELOG_VERSION_RE.match(line.strip())
        if m:
            versions.append(m.group(1))
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

    candidates: list[str] = list(args.versions)

    if args.from_tags:
        candidates.extend(from_git_tags())
    if args.from_changelog:
        candidates.extend(from_changelog(args.from_changelog))

    if not candidates:
        parser.print_help()
        return 1

    results = [validate(v) for v in candidates]

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        errors = 0
        for r in results:
            if r["valid"]:
                extras = ""
                if r.get("prerelease"):
                    extras += f" (pre-release: {r['prerelease']})"
                if r.get("buildmetadata"):
                    extras += f" (build: {r['buildmetadata']})"
                print(
                    f"PASS  {r['version']}  ->  {r['major']}.{r['minor']}.{r['patch']}{extras}"
                )
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
