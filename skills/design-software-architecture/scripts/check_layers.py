#!/usr/bin/env python3
"""Enforce allowed dependency directions between layers of a Python project.

Rules file (JSON):
  {"layers":  {"domain": ["orders/domain.py"], "adapters": ["orders/adapters/"]},
   "allowed": {"domain": [], "adapters": ["domain"]}}

A layer lists files, or directories ending with "/", relative to --root.
Each import of a module inside --root is resolved to its file, and to
that file's layer. An import from layer A into layer B is allowed when
A == B or B is in allowed[A]. Files in no layer are reported, so new
code cannot slip past the rules. Module-level import cycles are reported
too.

Usage: check_layers.py RULES.json [--root DIR] [--json]
Exit status: 0 no violations, 1 violations, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

EPILOG = """\
Exit status:
  0  no violations
  1  at least one violation (forbidden import, file in no layer, cycle)
  2  unreadable input: RULES is missing or not valid rules JSON, or a
     Python file under --root does not parse

Output: one line per violation, then "N violation(s)". --json prints
{"violations": [...], "count": N}; each violation has a "kind" of
"unassigned" (file), "direction" (file, line, layer, imports_layer,
target, allowed), or "cycle" (files).

Examples:
  python3 scripts/check_layers.py layers.json
  python3 scripts/check_layers.py layers.json --root . --json \\
    | jq '.violations[] | select(.kind == "direction")'
"""


def module_path(root: Path, module: str) -> Path | None:
    base = root.joinpath(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def imports(path: Path, root: Path) -> list[tuple[int, Path]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[int, Path]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        for name in names:
            target = module_path(root, name)
            if target is not None and target != path:
                found.append((node.lineno, target))
    return found


def layer_of(path: Path, root: Path, layers: dict[str, list[str]]) -> str | None:
    relative = path.relative_to(root).as_posix()
    for layer, members in layers.items():
        for member in members:
            if relative == member or (
                member.endswith("/") and relative.startswith(member)
            ):
                return layer
    return None


def find_cycles(graph: dict[Path, set[Path]]) -> list[list[Path]]:
    cycles: list[list[Path]] = []
    state: dict[Path, int] = {}

    def visit(node: Path, stack: list[Path]) -> None:
        state[node] = 1
        for nxt in sorted(graph.get(node, ())):
            if state.get(nxt) == 1:
                cycles.append([*stack[stack.index(nxt) :], nxt])
            elif nxt not in state:
                visit(nxt, [*stack, nxt])
        state[node] = 2

    for node in sorted(graph):
        if node not in state:
            visit(node, [node])
    return cycles


def check(rules: dict, root: Path) -> list[str]:
    return [describe(violation) for violation in violations(rules, root)]


def describe(violation: dict) -> str:
    if violation["kind"] == "unassigned":
        return f"{violation['file']}: in no layer"
    if violation["kind"] == "cycle":
        return f"import cycle: {' -> '.join(violation['files'])}"
    return (
        f"{violation['file']}:{violation['line']}: {violation['layer']} imports "
        f"{violation['imports_layer']} ({violation['target']}); "
        f"allowed: {violation['allowed']}"
    )


def violations(rules: dict, root: Path) -> list[dict]:
    layers = rules["layers"]
    allowed = rules["allowed"]
    problems: list[dict] = []
    graph: dict[Path, set[Path]] = {}
    files = sorted(
        p
        for member in layers.values()
        for m in member
        for p in ((root / m).rglob("*.py") if m.endswith("/") else [root / m])
    )
    for path in sorted(root.rglob("*.py")):
        if layer_of(path, root, layers) is None and any(
            path.relative_to(root).as_posix().startswith(m.split("/")[0] + "/")
            for member in layers.values()
            for m in member
        ):
            problems.append({"kind": "unassigned", "file": str(path.relative_to(root))})
    for path in files:
        source = layer_of(path, root, layers)
        for line, target in imports(path, root):
            graph.setdefault(path, set()).add(target)
            dest = layer_of(target, root, layers)
            if dest is None or source is None or dest == source:
                continue
            if dest not in allowed.get(source, []):
                problems.append(
                    {
                        "kind": "direction",
                        "file": str(path.relative_to(root)),
                        "line": line,
                        "layer": source,
                        "imports_layer": dest,
                        "target": str(target.relative_to(root)),
                        "allowed": allowed.get(source, []),
                    }
                )
    for cycle in find_cycles(graph):
        names = [str(p.relative_to(root)) for p in cycle]
        problems.append({"kind": "cycle", "files": names})
    return problems


def load_rules(path: Path) -> dict:
    rules = json.loads(path.read_text(encoding="utf-8"))
    for key in ("layers", "allowed"):
        if not isinstance(rules, dict) or not isinstance(rules.get(key), dict):
            raise ValueError(
                f'{path} needs a "{key}" object; expected '
                '{"layers": {LAYER: [PATH, ...]}, "allowed": {LAYER: [LAYER, ...]}}'
            )
    return rules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("rules", type=Path, help="layer rules JSON file")
    parser.add_argument(
        "--root",
        type=Path,
        help="project root the layer paths are relative to (default: RULES's folder)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        rules = load_rules(args.rules)
        root = (args.root or args.rules.parent).resolve()
        found = violations(rules, root)
    except SyntaxError as error:
        print(
            f"error: cannot parse {error.filename}:{error.lineno}: {error.msg}; "
            "fix the file or move it out of --root",
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"error: cannot read rules: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"violations": found, "count": len(found)}, indent=2))
        return 1 if found else 0
    problems = [describe(violation) for violation in found]
    for problem in problems:
        print(problem)
    print(f"{len(problems)} violation(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
