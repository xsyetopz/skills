#!/usr/bin/env python3
"""Check an implementation plan's structure and dependency graph.

Task format (a list item, continuation lines indented):

  - T3 [depends: T1, T2] [files: src/a.py, tests/test_a.py] Summary.
    Verify: `python3 -m unittest tests.test_a`
    Done when: <observable condition>.

Optional on the first line: `[estimate: 2h]` (h or d).

Reported defects: duplicate task IDs; dependencies on unknown or later
tasks (the list must be in an executable order); dependency cycles;
tasks without `Verify:` containing a backticked command, without
`Done when:`, or without `[files: ...]`; vague verbs in the summary.
Reported facts: task count, critical path (by estimate when every task
has one, else by task count), and the commands to run.

Usage: check_plan.py PLAN.md [--commands | --json]
Exit status: 0 no defects, 1 defects, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TASK = re.compile(r"^\s*[-*]\s+(T\d+)\b(.*)$")
DEPENDS = re.compile(r"\[depends:\s*([^\]]*)\]")
FILES = re.compile(r"\[files:\s*([^\]]+)\]")
ESTIMATE = re.compile(r"\[estimate:\s*(\d+(?:\.\d+)?)\s*([hd])\]")
VERIFY = re.compile(r"Verify:\s*`([^`]+)`")
DONE = re.compile(r"Done when:\s*\S")
EPILOG = """\
Exit status:
  0  no defects
  1  at least one defect (printed as "DEFECT T1: ...")
  2  the plan file is unreadable

Output: "tasks=N", the critical path when there are no defects, then one
"DEFECT" line per defect. --commands prints only the Verify commands, one
per line. --json prints {tasks, critical_path, defects, commands}, where
critical_path is {tasks, length, unit} or null when there are defects.

Examples:
  python3 scripts/check_plan.py PLAN.md
  python3 scripts/check_plan.py --commands PLAN.md | sort -u
  python3 scripts/check_plan.py --json PLAN.md | jq '.defects'
"""
VAGUE = (
    "as needed",
    "clean up",
    "etc",
    "handle",
    "improve",
    "misc",
    "optimize",
    "polish",
    "refactor",
    "various",
)


@dataclass
class Task:
    identifier: str
    line: int
    text: str
    depends: list[str] = field(default_factory=list)
    hours: float | None = None


def parse(text: str) -> list[Task]:
    tasks: list[Task] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = TASK.match(line)
        if match:
            tasks.append(Task(match.group(1), number, match.group(2).strip()))
        elif tasks and line.startswith("  ") and line.strip():
            tasks[-1].text += "\n" + line.strip()
        elif tasks and line.strip() and not line.startswith(" "):
            tasks.append(Task("", number, ""))  # end of the task's block
    return [task for task in tasks if task.identifier]


def analyze(tasks: list[Task]) -> tuple[list[str], list[str], list[str]]:
    defects: list[str] = []
    facts: list[str] = []
    commands: list[str] = []
    order = {task.identifier: index for index, task in enumerate(tasks)}
    if len(order) != len(tasks):
        seen: set[str] = set()
        for task in tasks:
            if task.identifier in seen:
                defects.append(f"{task.identifier}: duplicate task ID")
            seen.add(task.identifier)
    for index, task in enumerate(tasks):
        first_line = task.text.split("\n", 1)[0]
        depends = DEPENDS.search(first_line)
        if depends:
            task.depends = [d.strip() for d in depends.group(1).split(",")]
            task.depends = [d for d in task.depends if d and d != "-"]
        for dep in task.depends:
            if dep not in order:
                defects.append(f"{task.identifier}: depends on unknown {dep}")
            elif order[dep] >= index:
                defects.append(f"{task.identifier}: depends on later task {dep}")
        estimate = ESTIMATE.search(first_line)
        if estimate:
            value = float(estimate.group(1))
            task.hours = value * (8 if estimate.group(2) == "d" else 1)
        if not FILES.search(first_line):
            defects.append(f"{task.identifier}: no [files: ...]")
        verify = VERIFY.search(task.text)
        if verify:
            commands.append(verify.group(1))
        else:
            defects.append(f"{task.identifier}: no Verify: `command`")
        if not DONE.search(task.text):
            defects.append(f"{task.identifier}: no 'Done when:'")
        summary = re.sub(r"\[[^\]]*\]", "", first_line).lower()
        for word in VAGUE:
            if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", summary):
                defects.append(f"{task.identifier}: vague verb '{word}'")
    defects += find_cycles(tasks)
    if not defects:
        facts.append(critical_path(tasks))
    facts.insert(0, f"tasks={len(tasks)}")
    return defects, facts, commands


def find_cycles(tasks: list[Task]) -> list[str]:
    graph = {task.identifier: task.depends for task in tasks}
    state: dict[str, int] = {}
    cycles: list[str] = []

    def visit(node: str, path: list[str]) -> None:
        state[node] = 1
        for dep in graph.get(node, []):
            if state.get(dep) == 1:
                cycle = [*path[path.index(dep) :], dep] if dep in path else [dep]
                cycles.append("cycle: " + " -> ".join(cycle))
            elif state.get(dep, 0) == 0 and dep in graph:
                visit(dep, [*path, dep])
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            visit(node, [node])
    return cycles


def critical_path(tasks: list[Task]) -> str:
    chain, total, unit = critical_chain(tasks)
    unit = "h" if unit == "h" else " tasks"
    return f"critical path: {' -> '.join(chain)} ({total:g}{unit})"


def critical_chain(tasks: list[Task]) -> tuple[list[str], float, str]:
    """Longest dependency chain, its length, and the unit ("h" or "tasks")."""
    use_hours = all(task.hours is not None for task in tasks)
    length: dict[str, float] = {}
    previous: dict[str, str | None] = {}
    for task in tasks:  # listed order is a valid topological order here
        weight = task.hours if use_hours and task.hours is not None else 1.0
        best, via = 0.0, None
        for dep in task.depends:
            if length[dep] > best:
                best, via = length[dep], dep
        length[task.identifier] = best + weight
        previous[task.identifier] = via
    end = max(length, key=lambda key: length[key]) if length else None
    chain: list[str] = []
    while end:
        chain.append(end)
        end = previous[end]
    total = length[chain[0]] if chain else 0
    return list(reversed(chain)), total, "h" if use_hours else "tasks"


def report(tasks: list[Task], defects: list[str], commands: list[str]) -> dict:
    """The --json document; call after analyze(), which fills dependencies."""
    path = None
    if not defects:
        chain, total, unit = critical_chain(tasks)
        path = {"tasks": chain, "length": total, "unit": unit}
    entries = []
    for defect in defects:
        task, _, message = defect.partition(": ")
        if defect.startswith("cycle:"):
            task, message = None, defect
        entries.append({"task": task, "message": message})
    return {
        "tasks": len(tasks),
        "critical_path": path,
        "defects": entries,
        "commands": commands,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("plan", help="plan in Markdown (PLAN.md)")
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--commands", action="store_true", help="print only the Verify commands"
    )
    output.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        text = Path(args.plan).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read plan {args.plan}: {error}; "
            "expected a UTF-8 Markdown file",
            file=sys.stderr,
        )
        return 2
    tasks = parse(text)
    defects, facts, commands = analyze(tasks)
    if args.json:
        print(json.dumps(report(tasks, defects, commands), indent=2))
        return 1 if defects else 0
    if args.commands:
        print("\n".join(commands))
        return 1 if defects else 0
    for fact in facts:
        print(fact)
    for defect in defects:
        print(f"DEFECT {defect}")
    return 1 if defects else 0


if __name__ == "__main__":
    raise SystemExit(main())
