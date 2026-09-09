#!/usr/bin/env python3
"""Audit CHANGELOG.md against Keep a Changelog 1.1.0.

Usage:
    python3 audit_changelog.py [CHANGELOG_PATH] [--json]

Rules from https://keepachangelog.com/en/1.1.0/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

KEEP_A_CHANGELOG_SPEC = "https://keepachangelog.com/en/1.1.0/"
SEMVER_SPEC = "https://semver.org/"

VALID_CATEGORIES = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}

VERSION_HEADER_RE = re.compile(
    r"^##\s+\[(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)\]"
    r"\s*-\s*(\d{4}-\d{2}-\d{2})(?:\s*\[YANKED\])?\s*$"
)
UNRELEASED_RE = re.compile(r"^##\s+\[(?:U|u)nreleased\]")
CATEGORY_RE = re.compile(
    r"^###\s+(Added|Changed|Deprecated|Removed|Fixed|Security)\s*$"
)
ATTRIBUTION_RE = re.compile(r"keep\s*a\s*changelog", re.IGNORECASE)
SEMVER_REF_RE = re.compile(r"semantic\s*versioning", re.IGNORECASE)

# Semver validation regex (from semver.org)
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _read(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def _format_location(line_no: int | None = None) -> str:
    if line_no is not None:
        return f"line {line_no}"
    return ""


def audit(path: Path) -> dict:
    lines = _read(path)
    findings: list[dict] = []
    versions_found: list[str] = []

    if not lines:
        findings.append(
            {
                "severity": "error",
                "rule": "file-exists",
                "message": f"CHANGELOG.md not found or empty at {path}",
            }
        )
        return {"path": str(path), "findings": findings, "versions": versions_found}

    # Rule 1: H1 must be "# Changelog"
    h1 = lines[0].strip() if lines else ""
    if h1 != "# Changelog":
        findings.append(
            {
                "severity": "error",
                "rule": "h1-title",
                "location": "line 1",
                "message": f"H1 must be '# Changelog', found: {h1!r}",
                "spec": KEEP_A_CHANGELOG_SPEC,
            }
        )

    # Rule 2: Format attribution line must exist
    body_text = "\n".join(lines)
    if not ATTRIBUTION_RE.search(body_text):
        findings.append(
            {
                "severity": "error",
                "rule": "format-attribution",
                "message": "Missing Keep a Changelog format attribution line",
                "spec": KEEP_A_CHANGELOG_SPEC,
            }
        )
    if not SEMVER_REF_RE.search(body_text):
        findings.append(
            {
                "severity": "warning",
                "rule": "semver-reference",
                "message": "Missing Semantic Versioning reference in changelog header",
                "spec": SEMVER_SPEC,
            }
        )

    # Track current state
    current_version: str | None = None
    found_unreleased = False
    version_lines: dict[str, int] = {}
    categories_in_version: dict[str, set[str]] = {}
    prev_date: date | None = None
    prev_version: str | None = None

    for idx, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue

        # Detect unreleased section
        m = UNRELEASED_RE.match(line)
        if m:
            found_unreleased = True
            current_version = "Unreleased"
            version_lines[current_version] = idx
            categories_in_version[current_version] = set()
            continue

        # Detect version header
        m = VERSION_HEADER_RE.match(line)
        if m:
            version_str = m.group(1)
            date_str = m.group(2)
            if version_str is None or date_str is None:
                continue

            # Validate semver
            if not SEMVER_RE.match(version_str):
                findings.append(
                    {
                        "severity": "error",
                        "rule": "semver-format",
                        "location": f"line {idx}",
                        "message": f"Version '{version_str}' is not valid SemVer",
                        "spec": SEMVER_SPEC,
                    }
                )

            # Validate date
            try:
                parsed_date = date.fromisoformat(date_str)
                if prev_date and parsed_date > prev_date:
                    findings.append(
                        {
                            "severity": "error",
                            "rule": "reverse-chronological",
                            "location": f"line {idx}",
                            "message": (
                                f"Date {date_str} for {version_str} is newer than "
                                f"previous version {prev_version}. Entries must be "
                                f"reverse chronological."
                            ),
                            "spec": KEEP_A_CHANGELOG_SPEC,
                        }
                    )
                prev_date = parsed_date
            except ValueError:
                findings.append(
                    {
                        "severity": "error",
                        "rule": "date-format",
                        "location": f"line {idx}",
                        "message": f"Date '{date_str}' is not valid ISO 8601 (YYYY-MM-DD)",
                        "spec": KEEP_A_CHANGELOG_SPEC,
                    }
                )

            current_version = version_str
            prev_version = version_str
            version_lines[version_str] = idx
            categories_in_version[version_str] = set()
            versions_found.append(version_str)
            continue

        # Detect category heading
        m = CATEGORY_RE.match(line)
        if m:
            cat = m.group(1)
            if current_version and cat in categories_in_version.get(
                current_version, set()
            ):
                findings.append(
                    {
                        "severity": "error",
                        "rule": "duplicate-category",
                        "location": f"line {idx}",
                        "message": (
                            f"Duplicate category '### {cat}' in version "
                            f"{current_version}. Each category must appear at most once."
                        ),
                        "spec": KEEP_A_CHANGELOG_SPEC,
                    }
                )
            if current_version:
                categories_in_version[current_version].add(cat)
            continue

        # Detect invalid category names
        invalid_cat = re.match(r"^###\s+(\S+)", line)
        if invalid_cat:
            cat_name = invalid_cat.group(1)
            if cat_name not in VALID_CATEGORIES:
                findings.append(
                    {
                        "severity": "error",
                        "rule": "invalid-category",
                        "location": f"line {idx}",
                        "message": (
                            f"Invalid category '### {cat_name}'. Must be one of: "
                            f"{', '.join(sorted(VALID_CATEGORIES))}"
                        ),
                        "spec": KEEP_A_CHANGELOG_SPEC,
                    }
                )

        # Detect bullet entries
    # Rule: Unreleased section should exist for active projects
    if not found_unreleased:
        findings.append(
            {
                "severity": "warning",
                "rule": "missing-unreleased",
                "message": (
                    "No [Unreleased] section found. Active projects should track "
                    "unreleased changes."
                ),
                "spec": KEEP_A_CHANGELOG_SPEC,
            }
        )

    # Rule: No commit log dumps (heuristic: check for commit hashes in entries)
    commit_hash_re = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)
    for idx, raw in enumerate(lines, start=1):
        if raw.strip().startswith("- ") and commit_hash_re.search(raw):
            findings.append(
                {
                    "severity": "warning",
                    "rule": "commit-log-dump",
                    "location": f"line {idx}",
                    "message": (
                        "Entry contains a commit hash. Changelogs describe user-facing "
                        "changes, not commit references."
                    ),
                    "spec": KEEP_A_CHANGELOG_SPEC,
                }
            )

    # Rule: Every version must have at least one entry
    for ver, cats in categories_in_version.items():
        if not cats:
            findings.append(
                {
                    "severity": "error",
                    "rule": "empty-version",
                    "location": _format_location(version_lines.get(ver)),
                    "message": f"Version {ver} has no change categories.",
                    "spec": KEEP_A_CHANGELOG_SPEC,
                }
            )

    return {"path": str(path), "findings": findings, "versions": versions_found}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit CHANGELOG.md against Keep a Changelog 1.1.0."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="CHANGELOG.md",
        help="Path to CHANGELOG.md (default: CHANGELOG.md in cwd)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    changelog_path = Path(args.path).resolve()
    result = audit(changelog_path)

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        findings = result["findings"]
        if not findings:
            print(f"PASS: {changelog_path}")
            print(f"  Versions found: {len(result['versions'])}")
            if result["versions"]:
                print(f"  Latest: {result['versions'][0]}")
            return 0

        errors = [f for f in findings if f["severity"] == "error"]
        warnings = [f for f in findings if f["severity"] == "warning"]

        for f in findings:
            loc = f" ({f['location']})" if f.get("location") else ""
            print(f"{f['severity'].upper()}: {f['rule']}{loc}")
            print(f"  {f['message']}")

        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        print(f"Spec: {KEEP_A_CHANGELOG_SPEC}")

        if errors:
            return 1

    return int(any(f["severity"] == "error" for f in result["findings"]))


if __name__ == "__main__":
    sys.exit(main())
