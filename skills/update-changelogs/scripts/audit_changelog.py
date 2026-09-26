#!/usr/bin/env python3
"""Audit a Keep a Changelog + SemVer profile, not arbitrary release-note formats."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_semver import SEMVER_RE
from changelog_markdown import Section, release_header, sections

KEEP_A_CHANGELOG_SPEC = "https://keepachangelog.com/en/2.0.0/"
VALID_CATEGORIES = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error; an unreadable file is reported as a "file-read"
     error finding

Output: "PASS: PATH" with the version count and latest version, or one
"SEVERITY: rule (line N)" line plus an indented message per finding and
an "N error(s), N warning(s)" summary. --json prints {path, findings:
[{severity, rule, location, message}], versions}.

Examples:
  python3 scripts/audit_changelog.py
  python3 scripts/audit_changelog.py docs/CHANGELOG.md
  python3 scripts/audit_changelog.py CHANGELOG.md --json \\
    | jq '.findings[] | select(.severity == "error")'
"""


class Finding(TypedDict):
    severity: Literal["error", "warning"]
    rule: str
    location: str
    message: str


class AuditResult(TypedDict):
    path: str
    findings: list[Finding]
    versions: list[str]


def has_entries(document: list[Section], index: int) -> bool:
    section = document[index]
    if section.has_content:
        return True
    for child in document[index + 1 :]:
        if child.level <= section.level:
            break
        if child.has_content:
            return True
    return False


def audit(path: Path) -> AuditResult:
    findings: list[Finding] = []
    versions: list[str] = []
    result: AuditResult = {
        "path": str(path),
        "findings": findings,
        "versions": versions,
    }

    def report(
        rule: str,
        message: str,
        line: int = 1,
        severity: Literal["error", "warning"] = "error",
    ) -> None:
        findings.append(
            {
                "severity": severity,
                "rule": rule,
                "location": f"line {line}",
                "message": message,
            }
        )

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report("file-read", f"Cannot read {path}: {exc}")
        return result
    if not text.strip():
        report("empty-file", "The changelog is empty.")
        return result

    document = sections(text)
    if not document or document[0].level != 1 or document[0].title != "Changelog":
        report(
            "h1-title", "The recommended title is '# Changelog'.", severity="warning"
        )

    seen: set[str] = set()
    current: str | None = None
    categories: set[str] = set()
    previous_date: date | None = None
    for index, section in enumerate(document):
        match section.level:
            case 1:
                current = None
            case 2:
                version, released = release_header(section.title)
                current = (
                    "Unreleased" if version.casefold() == "unreleased" else version
                )
                categories = set()
                if current in seen:
                    report(
                        "duplicate-version",
                        f"Duplicate release section: {current}.",
                        section.line,
                    )
                seen.add(current)
                if current == "Unreleased":
                    if versions:
                        report(
                            "unreleased-order",
                            "Unreleased must precede released versions.",
                            section.line,
                        )
                    if released:
                        report(
                            "unreleased-date",
                            "Unreleased must not have a release date.",
                            section.line,
                        )
                    continue

                versions.append(version)
                if not SEMVER_RE.fullmatch(version):
                    report(
                        "semver-format",
                        f"Version {version!r} is not SemVer 2.0.0.",
                        section.line,
                    )
                if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", released):
                    report(
                        "date-format",
                        f"Invalid release date {released!r}; expected YYYY-MM-DD.",
                        section.line,
                    )
                else:
                    try:
                        parsed_date = date.fromisoformat(released)
                    except ValueError:
                        report(
                            "date-format",
                            f"Invalid release date {released!r}; expected YYYY-MM-DD.",
                            section.line,
                        )
                    else:
                        if previous_date and parsed_date > previous_date:
                            report(
                                "reverse-chronological",
                                "Release dates must be newest first.",
                                section.line,
                            )
                        previous_date = parsed_date

                # Content can be prose or grouped changes; headings alone are
                # not entries.
                if not has_entries(document, index):
                    report(
                        "empty-version",
                        f"Release {version} has no change entries.",
                        section.line,
                    )
            case 3:
                category = section.title
                if current is None:
                    report(
                        "orphan-category",
                        "A change category needs a release section.",
                        section.line,
                    )
                if category not in VALID_CATEGORIES:
                    report(
                        "invalid-category",
                        f"Unknown change category {category!r}.",
                        section.line,
                    )
                if category in categories:
                    report(
                        "duplicate-category",
                        f"Duplicate category {category!r} in {current}.",
                        section.line,
                    )
                categories.add(category)
                if not has_entries(document, index):
                    report(
                        "empty-category",
                        f"Omit empty category {category!r}.",
                        section.line,
                    )

    if "Unreleased" not in seen:
        report(
            "missing-unreleased",
            "An active project can track upcoming changes in Unreleased.",
            severity="warning",
        )
    if not seen:
        report(
            "missing-releases",
            "No release sections found; this audit expects top-level H2 releases.",
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the Keep a Changelog 2.0.0 + SemVer profile.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        print(f"Profile based on: {KEEP_A_CHANGELOG_SPEC}")

        if errors:
            return 1

    return int(any(f["severity"] == "error" for f in result["findings"]))


if __name__ == "__main__":
    sys.exit(main())
