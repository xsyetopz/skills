#!/usr/bin/env python3
"""Mutation testing for one Python file with any test command.

Each mutant changes one operator or constant in TARGET, is written into a
temporary copy of ROOT, and the test command runs there. A mutant is
killed when the command exits non-zero (or times out), and survives when
it exits 0. A survivor is a behavior change the tests did not notice:
a missing test, a weak assertion, or an equivalent mutant to justify.

Mutations:
  compare   <  <=  >  >=  ==  !=  in  not in  is  is not  (swapped)
  arith     +  -  (swapped), *  // (swapped)
  boolean   and  or  (swapped); `not x` becomes `x`
  constant  integer n becomes n + 1 (booleans untouched)
  return    `return expr` becomes `return None`

Usage:
  mutate.py TARGET --test "python3 -m unittest" [--root DIR]
            [--function NAME ...] [--timeout SECONDS] [--json] [--list]
Exit status: 0 no survivors, 1 survivors, 2 baseline failure or bad input.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

SWAPS: dict[type, type] = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv,
    ast.FloorDiv: ast.Mult,
    ast.And: ast.Or,
    ast.Or: ast.And,
}
IGNORED = {".git", "__pycache__", "node_modules", ".venv", ".mypy_cache"}
EPILOG = """\
Exit status:
  0  no survivors (or --list)
  1  at least one mutant survived
  2  bad input (TARGET outside --root, unreadable or unparsable, test
     command not found) or the tests fail before any mutation

Output: one "PATH:LINE: KIND: CHANGE: STATUS" line per mutant (status
killed, timeout, or survived), then "N killed, N survived, N total".
--json prints a list of {index, line, kind, change, status}. --list is a
dry run: it prints the mutants with status "pending" and runs nothing.
TARGET and ROOT are never modified; mutants run in a temporary copy.

Examples:
  python3 scripts/mutate.py src/pricing.py --test "python3 -m unittest"
  python3 scripts/mutate.py src/pricing.py --test "pytest -q" --function total
  python3 scripts/mutate.py src/pricing.py --test "pytest -q" --list
"""


@dataclass
class Mutant:
    index: int
    line: int
    kind: str
    change: str
    status: str = "pending"


Site = tuple[ast.AST, str, str, int]


def sites(tree: ast.AST, functions: set[str]) -> list[Site]:
    """Return (node, kind, change, operand index) per site, in walk order."""
    found: list[Site] = []

    def visit(node: ast.AST, inside: bool) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            inside = inside or not functions or node.name in functions
        if inside or not functions:
            found.extend(describe(node))
        for child in ast.iter_child_nodes(node):
            visit(child, inside)

    visit(tree, False)
    return found


def swap(op: ast.AST) -> str:
    return f"{type(op).__name__} -> {SWAPS[type(op)].__name__}"


def describe(node: ast.AST) -> list[Site]:
    if isinstance(node, ast.Compare):
        return [
            (node, "compare", swap(op), i)
            for i, op in enumerate(node.ops)
            if type(op) in SWAPS
        ]
    if isinstance(node, (ast.BinOp, ast.BoolOp)) and type(node.op) in SWAPS:
        kind = "boolean" if isinstance(node, ast.BoolOp) else "arith"
        return [(node, kind, swap(node.op), 0)]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return [(node, "boolean", "not x -> x", 0)]
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    ):
        return [(node, "constant", f"{node.value} -> {node.value + 1}", 0)]
    if isinstance(node, ast.Return) and node.value is not None:
        value = node.value
        if not (isinstance(value, ast.Constant) and value.value is None):
            return [(node, "return", "return expr -> return None", 0)]
    return []


def apply(node: ast.AST, operand: int) -> ast.AST:
    """Mutate node in place, or return a replacement node."""
    if isinstance(node, ast.Compare):
        node.ops[operand] = SWAPS[type(node.ops[operand])]()
    elif isinstance(node, (ast.BinOp, ast.BoolOp)):
        node.op = SWAPS[type(node.op)]()
    elif isinstance(node, ast.UnaryOp):
        return node.operand
    elif isinstance(node, ast.Constant) and isinstance(node.value, int):
        node.value = node.value + 1
    elif isinstance(node, ast.Return):
        node.value = ast.Constant(value=None)
    return node


def mutated_source(tree: ast.Module, index: int, functions: set[str]) -> str:
    clone = copy.deepcopy(tree)
    target, _, _, operand = sites(clone, functions)[index]
    replacement = apply(target, operand)
    if replacement is not target:
        for parent in ast.walk(clone):
            for field, value in ast.iter_fields(parent):
                if value is target:
                    setattr(parent, field, replacement)
                elif isinstance(value, list):
                    for position, item in enumerate(value):
                        if item is target:
                            value[position] = replacement
    return ast.unparse(ast.fix_missing_locations(clone)) + "\n"


def run(command: list[str], cwd: Path, timeout: float) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    return "survived" if result.returncode == 0 else "killed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", help="Python file to mutate (inside --root)")
    parser.add_argument("--test", required=True, help="test command, one string")
    parser.add_argument(
        "--root", default=".", help="project directory to copy (default: .)"
    )
    parser.add_argument(
        "--function",
        action="append",
        default=[],
        help="mutate only this function; repeatable",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="seconds per test run; a timeout counts as killed (default: 60)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON list")
    parser.add_argument(
        "--list", action="store_true", help="list the mutants without running tests"
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    target = Path(args.target).resolve()
    try:
        relative = target.relative_to(root)
        tree = ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    except ValueError:
        print(
            f"error: {target} is not inside --root {root}; pass --root with the "
            "project directory that contains TARGET",
            file=sys.stderr,
        )
        return 2
    except (OSError, SyntaxError) as error:
        print(f"error: cannot parse {target}: {error}", file=sys.stderr)
        return 2
    functions = set(args.function)
    mutants = [
        Mutant(i, getattr(node, "lineno", 0), kind, change)
        for i, (node, kind, change, _) in enumerate(sites(tree, functions))
    ]
    command = shlex.split(args.test)
    if args.list:
        if args.json:
            print(json.dumps([asdict(m) for m in mutants], indent=2))
        else:
            for m in mutants:
                print(f"{relative}:{m.line}: {m.kind}: {m.change}: {m.status}")
            print(f"{len(mutants)} mutant(s); tests not run")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "work"
        shutil.copytree(root, work, ignore=shutil.ignore_patterns(*IGNORED))
        copy_target = work / relative
        try:
            baseline = run(command, work, args.timeout)
        except OSError as error:
            print(
                f"error: cannot run --test {args.test!r}: {error}; "
                "pass a command that runs from --root",
                file=sys.stderr,
            )
            return 2
        if baseline != "survived":
            print("error: tests fail before mutation; fix them first", file=sys.stderr)
            return 2
        original = copy_target.read_text(encoding="utf-8")
        for mutant in mutants:
            copy_target.write_text(
                mutated_source(tree, mutant.index, functions), encoding="utf-8"
            )
            mutant.status = run(command, work, args.timeout)
        copy_target.write_text(original, encoding="utf-8")

    survivors = [m for m in mutants if m.status == "survived"]
    if args.json:
        print(json.dumps([asdict(m) for m in mutants], indent=2))
    else:
        for m in mutants:
            print(f"{relative}:{m.line}: {m.kind}: {m.change}: {m.status}")
        killed = sum(m.status in {"killed", "timeout"} for m in mutants)
        print(f"{killed} killed, {len(survivors)} survived, {len(mutants)} total")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
