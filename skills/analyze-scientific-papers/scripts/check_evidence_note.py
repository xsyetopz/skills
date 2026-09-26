#!/usr/bin/env python3
"""Check an evidence note (assets/evidence-note-template.md format).

Rules:
  - every field is present: Claim, Search, Source, Updates, Status,
    Evidence, Stats, Conclusion;
  - Status is one of: metadata, abstract, full text, code or data;
  - Conclusion starts with supported, contradicted, or unresolved;
  - a supported or contradicted conclusion needs Status "full text" or
    "code or data" (metadata and abstracts are not evidence), and an
    Evidence field that names a section, table, figure, or page;
  - Source carries a DOI (10.x/...) or an arXiv ID with a version (vN);
  - Updates is filled in (the corrections/retractions lookup was done).

Usage: check_evidence_note.py NOTE.md... [--json]
Exit status: 0 all notes pass, 1 problems found, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FIELDS = [
    "Claim",
    "Search",
    "Source",
    "Updates",
    "Status",
    "Evidence",
    "Stats",
    "Conclusion",
]
STATUSES = {"metadata", "abstract", "full text", "code or data"}
DECISIVE = {"supported", "contradicted"}
EPILOG = """\
Output: "NOTE: problem" per problem, or "NOTE: ok". --json prints
{"notes": [{file, ok, problems}], "failed": N}. An unreadable note stops
the run with exit 2 (earlier notes are still reported in text mode).

Examples:
  python3 scripts/check_evidence_note.py notes/claim-1.md
  python3 scripts/check_evidence_note.py notes/*.md --json \\
    | jq '.notes[] | select(.ok | not)'
"""
LOCATION = re.compile(r"\b(section|sec\.|table|fig(ure)?\.?|page|p\.)\s*\S+", re.I)
IDENTIFIER = re.compile(
    r"\b10\.\d{4,9}/\S+|\barXiv:\s*\d{4}\.\d{4,5}v\d+|\b\d{4}\.\d{4,5}v\d+", re.I
)


def fields(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        match = re.match(r"^([A-Z][a-z]+):\s*(.*)$", line)
        if match and match.group(1) in FIELDS:
            current = match.group(1)
            found[current] = match.group(2).strip()
        elif current and line.strip():
            found[current] += " " + line.strip()
    return found


def check(text: str) -> list[str]:
    note = fields(text)
    problems = [f"missing field {name}" for name in FIELDS if not note.get(name)]
    status = note.get("Status", "").lower()
    if status and status not in STATUSES:
        problems.append(f"status {status!r} not in {sorted(STATUSES)}")
    conclusion = note.get("Conclusion", "").lower().split(",")[0].split()[:1]
    verdict = conclusion[0] if conclusion else ""
    if verdict and verdict not in DECISIVE | {"unresolved"}:
        problems.append(
            f"conclusion {verdict!r} is not supported/contradicted/unresolved"
        )
    if verdict in DECISIVE:
        if status in {"metadata", "abstract"}:
            problems.append(f"{verdict} from {status} only: read the full text first")
        if not LOCATION.search(note.get("Evidence", "")):
            problems.append("evidence names no section, table, figure, or page")
    if note.get("Source") and not IDENTIFIER.search(note["Source"]):
        problems.append("source has no DOI or versioned arXiv ID")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        usage="check_evidence_note.py [-h] [--json] NOTE.md...",
        description=(__doc__ or "").strip(),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", metavar="NOTE.md", help="evidence note")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit:  # keep main() returning a status for callers
        return int(exit.code or 0)
    failed = 0
    notes: list[dict] = []
    for raw in args.paths:
        try:
            problems = check(Path(raw).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as error:
            print(
                f"error: cannot read {raw}: {error}; expected a UTF-8 evidence note "
                "(assets/evidence-note-template.md format)",
                file=sys.stderr,
            )
            return 2
        notes.append({"file": raw, "ok": not problems, "problems": problems})
        failed += bool(problems)
        if args.json:
            continue
        for problem in problems:
            print(f"{raw}: {problem}")
        if not problems:
            print(f"{raw}: ok")
    if args.json:
        print(json.dumps({"notes": notes, "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
