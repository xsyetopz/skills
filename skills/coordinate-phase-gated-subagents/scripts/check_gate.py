#!/usr/bin/env python3
"""Decide whether a phase gate may close, from its evidence record.

Input JSON:
  {"phase": "integration-verification",
   "conditions": [{"id": "C1", "required": true,
                   "evidence": {"status": "passed", "command": "...",
                                "result": "..."}}],
   "requirements": [{"id": "R1", "verified_by": ["C1"]}]}

Status is one of: passed, failed, unavailable, not_run. Only "passed"
counts. The gate closes when every required condition passed and every
requirement is verified by at least one condition that passed. Failed,
unavailable, and not-run evidence are reported separately, because each
needs a different next step (fix, obtain access, run).

Usage: check_gate.py GATE.json [--json]
Exit status: 0 gate may close, 1 gate stays open (reasons printed),
2 unreadable or malformed input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STATUSES = {"passed", "failed", "unavailable", "not_run"}
EPILOG = """\
Output: "gate PHASE: may close", or "gate PHASE: OPEN" followed by one
indented reason per line. --json prints {"phase", "may_close", "reasons"}.

Examples:
  python3 scripts/check_gate.py gates/verification.json
  python3 scripts/check_gate.py gates/verification.json --json | jq '.reasons'
"""


def evaluate(gate: dict) -> list[str]:
    reasons: list[str] = []
    conditions = {c["id"]: c for c in gate["conditions"]}
    for condition in gate["conditions"]:
        evidence = condition.get("evidence") or {}
        status = evidence.get("status", "not_run")
        if status not in STATUSES:
            raise ValueError(f"{condition['id']}: unknown status {status!r}")
        if status == "passed" and not evidence.get("command"):
            reasons.append(f"{condition['id']}: passed without a recorded command")
        if condition.get("required", True) and status != "passed":
            reasons.append(f"{condition['id']}: {status}")
    for requirement in gate.get("requirements", []):
        verifying = [
            v
            for v in requirement.get("verified_by", [])
            if (conditions.get(v, {}).get("evidence") or {}).get("status") == "passed"
        ]
        unknown = [v for v in requirement.get("verified_by", []) if v not in conditions]
        if unknown:
            reasons.append(f"{requirement['id']}: unknown conditions {unknown}")
        if not verifying:
            reasons.append(f"{requirement['id']}: no passed verification")
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        usage="check_gate.py [-h] [--json] GATE.json",
        description=(__doc__ or "").strip(),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("gate", metavar="GATE.json", help="gate evidence record")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit:  # keep main() returning a status for callers
        return int(exit.code or 0)
    try:
        gate = json.loads(Path(args.gate).read_text(encoding="utf-8"))
        reasons = evaluate(gate)
    except KeyError as error:
        print(
            f"error: missing key {error}; expected {{'conditions': [{{'id': ...}}]}}"
            " and requirements with an 'id' (see --help)",
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(f"error: cannot check {args.gate}: {error}", file=sys.stderr)
        return 2
    phase = gate.get("phase", "?")
    if args.json:
        report = {"phase": phase, "may_close": not reasons, "reasons": reasons}
        print(json.dumps(report, indent=2))
        return 1 if reasons else 0
    if reasons:
        print(f"gate {phase}: OPEN")
        for reason in reasons:
            print(f"  {reason}")
        return 1
    print(f"gate {phase}: may close")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
