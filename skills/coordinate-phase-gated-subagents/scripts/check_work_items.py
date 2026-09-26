#!/usr/bin/env python3
"""Check a subagent work plan and print the parallel waves it allows.

Input JSON:
  {"phase": "implementation",
   "items": [{"id": "api", "phase": "implementation",
              "owns": ["src/api/"], "depends_on": []}, ...]}

`owns` lists the paths an item may write: a directory ends with "/",
anything else is one file. Two items may run in parallel only if neither
depends (directly or transitively) on the other AND their owned paths
do not overlap.

Errors: duplicate or unknown ids, dependency cycles, items from another
phase (parallel work stays inside the current phase), and overlapping
ownership between items that could run at the same time.

Usage: check_work_items.py PLAN.json [--json]
Exit status: 0 plan is safe (waves printed), 1 errors, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

EPILOG = """\
Exit status:
  0  the plan is safe; its waves are printed
  1  errors (duplicate or unknown ids, cycle, other phase, shared paths)
  2  unreadable input: PLAN is missing, not JSON, or lacks required keys

Output: "error: ..." lines, "wave N: a, b" lines, then "N error(s)".
--json prints {"errors": [...], "waves": [[ids], ...]}.

Examples:
  python3 scripts/check_work_items.py plan/work-items.json
  python3 scripts/check_work_items.py plan/work-items.json --json | jq '.waves'
"""


def overlaps(a: str, b: str) -> bool:
    """True when one owned path contains or equals the other."""

    def contains(directory: str, other: str) -> bool:
        return directory.endswith("/") and other.startswith(directory)

    return a == b or contains(a, b) or contains(b, a)


def ancestors(items: dict[str, dict]) -> dict[str, set[str]]:
    """Map each id to every id it depends on, transitively."""
    result: dict[str, set[str]] = {}

    def visit(node: str, stack: tuple[str, ...]) -> set[str]:
        if node in result:
            return result[node]
        if node in stack:
            raise ValueError("dependency cycle: " + " -> ".join((*stack, node)))
        found: set[str] = set()
        for parent in items[node].get("depends_on", []):
            found |= {parent} | visit(parent, (*stack, node))
        result[node] = found
        return found

    for node in items:
        visit(node, ())
    return result


def check(plan: dict) -> tuple[list[str], list[list[str]]]:
    errors: list[str] = []
    phase = plan.get("phase")
    raw = plan.get("items", [])
    ids = [item.get("id") for item in raw]
    for duplicate in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate id {duplicate!r}")
    items = {item["id"]: item for item in raw}
    for item in raw:
        for dependency in item.get("depends_on", []):
            if dependency not in items:
                errors.append(f"{item['id']}: unknown dependency {dependency!r}")
    if errors:
        return errors, []  # structure is broken: no waves can be computed
    for item in raw:
        if item.get("phase") != phase:
            errors.append(
                f"{item['id']}: phase {item.get('phase')!r} is not the current "
                f"phase {phase!r}"
            )
    try:
        before = ancestors(items)
    except ValueError as error:
        return [str(error)], []
    for a, b in combinations(sorted(items), 2):
        if a in before[b] or b in before[a]:
            continue  # ordered by dependencies: never concurrent
        for path_a in items[a].get("owns", []):
            for path_b in items[b].get("owns", []):
                if overlaps(path_a, path_b):
                    errors.append(
                        f"{a} and {b} can run in parallel but both own "
                        f"{path_a!r} / {path_b!r}"
                    )
    waves: list[list[str]] = []
    done: set[str] = set()
    while len(done) < len(items):
        ready = sorted(
            i
            for i in items
            if i not in done and set(items[i].get("depends_on", [])) <= done
        )
        waves.append(ready)
        done |= set(ready)
    return errors, waves


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("plan", type=Path, help="work plan JSON (see the format above)")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        errors, waves = check(plan)
    except KeyError as error:
        print(
            f"error: an item lacks the {error} key; expected "
            '{"phase": ..., "items": [{"id", "phase", "owns", "depends_on"}]}',
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(
            f"error: cannot check {args.plan}: {error}; expected a work plan JSON "
            "object",
            file=sys.stderr,
        )
        return 2
    if args.json:
        print(json.dumps({"errors": errors, "waves": waves}, indent=2))
    else:
        for message in errors:
            print(f"error: {message}")
        for number, wave in enumerate(waves, 1):
            print(f"wave {number}: {', '.join(wave)}")
        print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
