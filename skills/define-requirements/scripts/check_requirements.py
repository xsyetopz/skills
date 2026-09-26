#!/usr/bin/env python3
"""Check a Markdown requirements document for measurable defects.

Recognized lines (list items or paragraphs):

  REQ-<ID> [source: <text>] <EARS statement>
  AC-<ID> verifies REQ-<ID>[, REQ-<ID>...]: Given ..., when ..., then ...
  DEC-<ID>: <open decision>          (optional)

An EARS statement uses "shall" and one of the patterns
(Mavin et al., "Easy Approach to Requirements Syntax", RE'09):

  ubiquitous      The <system> shall <response>.
  event-driven    When <trigger>, the <system> shall <response>.
  state-driven    While <state>, the <system> shall <response>.
  unwanted        If <condition>, then the <system> shall <response>.
  optional        Where <feature>, the <system> shall <response>.
  complex         While ..., when ..., the <system> shall <response>.

Reported defects: duplicate IDs, requirements without a source, statements
that match no EARS pattern or contain several "shall", vague words, open
"TBD" markers, requirements that no acceptance criterion verifies, and
acceptance criteria that reference unknown requirements or lack
Given/When/Then.

Usage: check_requirements.py FILE [--json]
Exit status: 0 no defects, 1 defects found, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

EPILOG = """\
Exit status:
  0  no defects
  1  at least one defect (printed as "DEFECT ...")
  2  the file is unreadable

Output: a summary line "requirements=N acceptance_criteria=N defects=N",
EARS pattern counts, then one "DEFECT" line per defect. --json prints
{requirements, acceptance_criteria, patterns, defects}.

Examples:
  python3 scripts/check_requirements.py docs/specs/export.md
  python3 scripts/check_requirements.py --json docs/specs/export.md \\
    | jq '.patterns'
"""
REQ = re.compile(r"^\s*(?:[-*]\s+)?(REQ-[A-Z0-9-]+)\s+(.*)$")
AC = re.compile(
    r"^\s*(?:[-*]\s+)?(AC-[A-Z0-9-]+)\s+verifies\s+"
    r"((?:REQ-[A-Z0-9-]+)(?:\s*,\s*REQ-[A-Z0-9-]+)*)\s*:\s*(.*)$"
)
SOURCE = re.compile(r"^\[source:\s*([^\]]+)\]\s*(.*)$")
PATTERNS = {
    "complex": re.compile(r"^While .+, when .+, the .+ shall .+\.$"),
    "event-driven": re.compile(r"^When .+, the .+ shall .+\.$"),
    "state-driven": re.compile(r"^While .+, the .+ shall .+\.$"),
    "unwanted": re.compile(r"^If .+, then the .+ shall .+\.$"),
    "optional": re.compile(r"^Where .+, the .+ shall .+\.$"),
    "ubiquitous": re.compile(r"^The .+ shall .+\.$"),
}
VAGUE = (
    "appropriate",
    "appropriately",
    "as needed",
    "adequate",
    "and/or",
    "easy",
    "efficient",
    "etc",
    "fast",
    "flexible",
    "intuitive",
    "quickly",
    "reasonable",
    "robust",
    "seamless",
    "user-friendly",
)


@dataclass
class Report:
    requirements: int = 0
    acceptance_criteria: int = 0
    patterns: dict[str, int] = field(default_factory=dict)
    defects: list[str] = field(default_factory=list)


def classify(statement: str) -> str | None:
    for name, pattern in PATTERNS.items():
        if pattern.match(statement):
            return name
    return None


def vague_words(text: str) -> list[str]:
    lowered = text.lower()
    return [
        w for w in VAGUE if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", lowered)
    ]


def logical_lines(text: str) -> list[tuple[int, str]]:
    """Join wrapped list items and paragraphs; skip fenced code blocks."""
    joined: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        continuation = line.startswith("  ") and line.strip() and joined
        if continuation and not re.match(r"^\s*[-*]\s", line):
            start, previous = joined[-1]
            joined[-1] = (start, f"{previous} {line.strip()}")
        else:
            joined.append((number, line))
    return joined


def check(text: str) -> Report:
    report = Report()
    requirement_ids: list[str] = []
    verified: set[str] = set()
    ac_refs: list[tuple[str, list[str]]] = []
    for number, line in logical_lines(text):
        where = f"line {number}"
        if "TBD" in line:
            report.defects.append(f"{where}: open TBD marker")
        ac = AC.match(line)
        if ac:
            report.acceptance_criteria += 1
            refs = [r.strip() for r in ac.group(2).split(",")]
            ac_refs.append((ac.group(1), refs))
            body = ac.group(3).lower()
            if not all(k in body for k in ("given", "when", "then")):
                report.defects.append(f"{where}: {ac.group(1)} lacks Given/When/Then")
            continue
        req = REQ.match(line)
        if not req:
            continue
        identifier, rest = req.group(1), req.group(2).strip()
        report.requirements += 1
        requirement_ids.append(identifier)
        source = SOURCE.match(rest)
        if source:
            statement = source.group(2).strip()
        else:
            statement = rest
            report.defects.append(f"{where}: {identifier} has no [source: ...]")
        if statement.lower().count(" shall ") != 1:
            report.defects.append(
                f"{where}: {identifier} must contain exactly one 'shall'"
            )
        kind = classify(statement)
        if kind is None:
            report.defects.append(f"{where}: {identifier} matches no EARS pattern")
        else:
            report.patterns[kind] = report.patterns.get(kind, 0) + 1
        for word in vague_words(statement):
            report.defects.append(f"{where}: {identifier} uses vague term '{word}'")

    seen: set[str] = set()
    for identifier in requirement_ids:
        if identifier in seen:
            report.defects.append(f"{identifier}: duplicate ID")
        seen.add(identifier)
    for ac_id, refs in ac_refs:
        for ref in refs:
            if ref not in seen:
                report.defects.append(f"{ac_id}: references unknown {ref}")
            verified.add(ref)
    for identifier in sorted(seen - verified):
        report.defects.append(f"{identifier}: no acceptance criterion verifies it")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="requirements document in Markdown")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {args.file}: {error}; "
            "expected a UTF-8 Markdown requirements document",
            file=sys.stderr,
        )
        return 2
    report = check(text)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(
            f"requirements={report.requirements} "
            f"acceptance_criteria={report.acceptance_criteria} "
            f"defects={len(report.defects)}"
        )
        for kind, count in sorted(report.patterns.items()):
            print(f"  pattern {kind}: {count}")
        for defect in report.defects:
            print(f"  DEFECT {defect}")
    return 1 if report.defects else 0


if __name__ == "__main__":
    raise SystemExit(main())
