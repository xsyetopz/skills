"""Check a Markdown security review for incomplete findings.

Usage: python3 check_findings.py REVIEW.md [--json]

A finding is a heading ``### F<n>: <title>`` followed by ``- Field: value``
bullets (continuation lines indented by two spaces). The script reports, per finding, every required field that is
missing or malformed, validates any CVSS v3.1 or v4.0 vector against the
FIRST vector-string tables, and exits 1 if any finding has a problem.
It checks structure only; it cannot tell whether a trace is true.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DESCRIPTION = "Check a Markdown security review for incomplete findings."
EPILOG = """\
Exit status:
  0  every finding is complete
  1  at least one finding is incomplete
  2  no "### F<n>: title" findings, or REVIEW cannot be read

Output: "F1: OK" or "F1: problem; problem" per finding, then "N
finding(s), N incomplete". --json prints {"findings": {ID: [problems]},
"incomplete": N}.

Examples:
  python3 scripts/check_findings.py review.md
  python3 scripts/check_findings.py review.md --json | jq '.findings'
"""

HEADING = re.compile(r"^###\s+(F\d+):\s*(.+?)\s*$")
FIELD = re.compile(r"^-\s+([A-Za-z ]+):\s*(.*)$")
REQUIRED = (
    "CWE",
    "Location",
    "Status",
    "Preconditions",
    "Trace",
    "Impact",
    "Evidence",
    "Remediation",
    "Verification",
)
STATUSES = {"confirmed", "design risk", "hypothesis"}
CWE_ID = re.compile(r"\bCWE-\d+\b")
LOCATION = re.compile(r"\S+:\d+")
VECTOR = re.compile(r"CVSS:\d\.\d(?:/[A-Za-z]+:[A-Za-z]+)+")

# FIRST CVSS v3.1 specification, Table 15 (metric order as listed).
CVSS31 = {
    "AV": "NALP", "AC": "LH", "PR": "NLH", "UI": "NR", "S": "UC",
    "C": "HLN", "I": "HLN", "A": "HLN",
    "E": "XHFPU", "RL": "XUWTO", "RC": "XCRU",
    "CR": "XHML", "IR": "XHML", "AR": "XHML",
    "MAV": "XNALP", "MAC": "XLH", "MPR": "XNLH", "MUI": "XNR",
    "MS": "XUC", "MC": "XNLH", "MI": "XNLH", "MA": "XNLH",
}  # fmt: skip
BASE31 = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")

# FIRST CVSS v4.0 specification, Table 23; order is mandatory in v4.0.
CVSS40: dict[str, tuple[str, ...]] = {
    "AV": ("N", "A", "L", "P"), "AC": ("L", "H"), "AT": ("N", "P"),
    "PR": ("N", "L", "H"), "UI": ("N", "P", "A"),
    "VC": ("H", "L", "N"), "VI": ("H", "L", "N"), "VA": ("H", "L", "N"),
    "SC": ("H", "L", "N"), "SI": ("H", "L", "N"), "SA": ("H", "L", "N"),
    "E": ("X", "A", "P", "U"),
    "CR": ("X", "H", "M", "L"), "IR": ("X", "H", "M", "L"),
    "AR": ("X", "H", "M", "L"),
    "MAV": ("X", "N", "A", "L", "P"), "MAC": ("X", "L", "H"),
    "MAT": ("X", "N", "P"), "MPR": ("X", "N", "L", "H"),
    "MUI": ("X", "N", "P", "A"),
    "MVC": ("X", "N", "L", "H"), "MVI": ("X", "N", "L", "H"),
    "MVA": ("X", "N", "L", "H"), "MSC": ("X", "N", "L", "H"),
    "MSI": ("X", "N", "L", "H", "S"), "MSA": ("X", "N", "L", "H", "S"),
    "S": ("X", "N", "P"), "AU": ("X", "N", "Y"),
    "R": ("X", "A", "U", "I"), "V": ("X", "D", "C"),
    "RE": ("X", "L", "M", "H"),
    "U": ("X", "Clear", "Green", "Amber", "Red"),
}  # fmt: skip
BASE40 = ("AV", "AC", "AT", "PR", "UI", "VC", "VI", "VA", "SC", "SI", "SA")


def vector_problems(vector: str) -> list[str]:
    head, _, rest = vector.partition("/")
    pairs = [part.split(":", 1) for part in rest.split("/")] if rest else []
    if any(len(pair) != 2 for pair in pairs):
        return [f"malformed metric in {vector}"]
    names = [name for name, _ in pairs]
    problems: list[str] = []
    if len(set(names)) != len(names):
        problems.append("a metric appears more than once")
    if head == "CVSS:3.1":
        table: dict[str, tuple[str, ...]] = {k: tuple(v) for k, v in CVSS31.items()}
        base = BASE31
    elif head == "CVSS:4.0":
        table, base = CVSS40, BASE40
        order = [n for n in CVSS40 if n in names]
        if names != order:
            problems.append("v4.0 metrics are out of the mandatory order")
    else:
        return [f"unsupported version {head!r} (use CVSS:3.1 or CVSS:4.0)"]
    missing = [name for name in base if name not in names]
    if missing:
        problems.append("missing base metric(s) " + ",".join(missing))
    for name, value in pairs:
        if name not in table:
            problems.append(f"unknown metric {name}")
        elif value not in table[name]:
            problems.append(f"{name}:{value} is not an allowed value")
    return problems


def parse(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    last = ""
    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading:
            findings.append({"id": heading[1], "title": heading[2]})
            last = ""
            continue
        field = FIELD.match(line)
        if field and findings:
            last = field[1].strip()
            findings[-1][last] = field[2].strip()
        elif last and line.startswith("  ") and line.strip():
            findings[-1][last] += " " + line.strip()  # wrapped bullet
        else:
            last = ""
    return findings


def problems_for(finding: dict[str, str]) -> list[str]:
    problems = [f"missing {f}" for f in REQUIRED if not finding.get(f)]
    if finding.get("CWE") and not CWE_ID.search(finding["CWE"]):
        problems.append("CWE field has no CWE-<number> identifier")
    if finding.get("Location") and not LOCATION.search(finding["Location"]):
        problems.append("Location has no path:line")
    status = finding.get("Status", "").lower()
    if status and status not in STATUSES:
        problems.append(f"Status must be one of {sorted(STATUSES)}")
    if finding.get("Trace") and "->" not in finding["Trace"]:
        problems.append("Trace must show source -> ... -> sink")
    for vector in VECTOR.findall(finding.get("Severity", "")):
        problems.extend(vector_problems(vector))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("review", type=Path, help="security review in Markdown")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        findings = parse(args.review.read_text())
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {args.review}: {error}; expected a Markdown review "
            "with '### F<n>: title' findings",
            file=sys.stderr,
        )
        return 2
    report = {f["id"]: problems_for(f) for f in findings}
    incomplete = sum(1 for p in report.values() if p)
    if args.json:
        print(json.dumps({"findings": report, "incomplete": incomplete}))
    else:
        for finding_id, problems in report.items():
            print(f"{finding_id}: {'OK' if not problems else '; '.join(problems)}")
        print(f"{len(findings)} finding(s), {incomplete} incomplete")
    if not findings:
        print("no '### F<n>: title' findings found", file=sys.stderr)
        return 2
    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
