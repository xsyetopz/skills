#!/usr/bin/env python3
"""Report per-function readability metrics for Python source files.

Metrics (per function or method; nested functions are reported separately):
  nloc     non-blank, non-comment lines from `def` to the last body line
  ccn      cyclomatic complexity: 1 + decision points (if/elif, loops,
           conditional expressions, except handlers, match cases,
           comprehension `for`/`if` clauses, and each extra operand of
           `and`/`or`)
  nesting  deepest block nesting inside the body; an `elif` chain stays at
           one level, and nested `def`/`class`/`lambda` bodies are excluded
  params   parameters, excluding `self`/`cls` on methods

Usage:
  python_function_metrics.py [--max-nloc N] [--max-ccn N]
                             [--max-nesting N] [--max-params N]
                             [--json] [--limit N] PATH...

PATH may be a file or a directory (searched recursively for *.py).
Exit status: 0 all within limits, 1 a limit was exceeded, 2 bad input.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

BLOCKS = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Match,
)
DECISIONS = (
    ast.If,
    ast.IfExp,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.match_case,
)
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


@dataclass(frozen=True)
class FunctionMetrics:
    path: str
    name: str
    line: int
    nloc: int
    ccn: int
    nesting: int
    params: int


def count_params(node: ast.FunctionDef | ast.AsyncFunctionDef, is_method: bool) -> int:
    arguments = node.args
    names = [a.arg for a in arguments.posonlyargs + arguments.args]
    total = len(names) + len(arguments.kwonlyargs)
    total += int(arguments.vararg is not None) + int(arguments.kwarg is not None)
    if is_method and names and names[0] in ("self", "cls"):
        total -= 1
    return total


def walk_function_body(node: ast.AST):
    """Yield descendants of a function, not entering nested scopes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPES):
            continue
        yield child
        yield from walk_function_body(child)


def cyclomatic_complexity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    decisions = 0
    for child in walk_function_body(node):
        if isinstance(child, DECISIONS):
            decisions += 1
        elif isinstance(child, ast.BoolOp):
            decisions += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            decisions += 1 + len(child.ifs)
    return 1 + decisions


def max_nesting(statements: list[ast.stmt], depth: int = 0) -> int:
    deepest = depth
    for statement in statements:
        if isinstance(statement, SCOPES):
            continue
        if isinstance(statement, BLOCKS):
            deepest = max(deepest, nested_block_depth(statement, depth + 1))
    return deepest


def nested_block_depth(block: ast.stmt, depth: int) -> int:
    deepest = depth
    if isinstance(block, ast.If):
        deepest = max(deepest, max_nesting(block.body, depth))
        orelse = block.orelse
        is_elif = len(orelse) == 1 and isinstance(orelse[0], ast.If)
        if is_elif:
            deepest = max(deepest, nested_block_depth(orelse[0], depth))
        else:
            deepest = max(deepest, max_nesting(orelse, depth))
        return deepest
    if isinstance(block, ast.Try):
        groups = [block.body, block.orelse, block.finalbody]
        groups += [handler.body for handler in block.handlers]
    elif isinstance(block, ast.Match):
        groups = [case.body for case in block.cases]
    else:
        groups = [getattr(block, "body", []), getattr(block, "orelse", [])]
    for group in groups:
        deepest = max(deepest, max_nesting(group, depth))
    return deepest


def code_lines(lines: list[str], start: int, end: int) -> int:
    count = 0
    for text in lines[start - 1 : end]:
        stripped = text.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def analyze_file(path: Path) -> list[FunctionMetrics]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    lines = source.splitlines()
    results: list[FunctionMetrics] = []

    def visit(node: ast.AST, parent_is_class: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = child.end_lineno or child.lineno
                results.append(
                    FunctionMetrics(
                        path=str(path),
                        name=child.name,
                        line=child.lineno,
                        nloc=code_lines(lines, child.lineno, end),
                        ccn=cyclomatic_complexity(child),
                        nesting=max_nesting(child.body),
                        params=count_params(child, parent_is_class),
                    )
                )
                visit(child, parent_is_class=False)
            else:
                visit(child, parent_is_class=isinstance(child, ast.ClassDef))

    visit(tree, parent_is_class=False)
    return results


def python_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(
                f"{raw} does not exist; pass Python files or directories"
            )
    return files


EPILOG = """\
Exit status:
  0  every function is within the given limits (or no limit was given)
  1  at least one function exceeds a limit (marked "!!")
  2  a PATH does not exist, or a file does not parse or is not UTF-8

Output: a header, then one row per function: nloc, ccn, nesting, params,
PATH:LINE NAME, and "!! field value > limit" when a limit is exceeded.
--json prints a list of {path, line, name, nloc, ccn, nesting, params,
exceeded}. --limit N prints at most N rows (the exit status still covers
all functions) and notes the omission on stderr.

Examples:
  python3 scripts/python_function_metrics.py src
  python3 scripts/python_function_metrics.py --max-ccn 10 --max-nesting 3 src
  python3 scripts/python_function_metrics.py --json src \\
    | jq 'sort_by(-.ccn) | .[:10]'
"""


def exceeded(metrics: FunctionMetrics, limits: dict[str, int | None]) -> list[str]:
    problems = []
    for field, limit in limits.items():
        value = getattr(metrics, field)
        if limit is not None and value > limit:
            problems.append(f"{field} {value} > {limit}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="Python files or directories")
    parser.add_argument("--max-nloc", type=int, help="limit on nloc")
    parser.add_argument("--max-ccn", type=int, help="limit on cyclomatic complexity")
    parser.add_argument("--max-nesting", type=int, help="limit on block nesting")
    parser.add_argument("--max-params", type=int, help="limit on parameters")
    parser.add_argument("--json", action="store_true", help="print a JSON list")
    parser.add_argument(
        "--limit", type=int, metavar="N", help="print at most N functions"
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be 0 or more")
    limits = {
        "nloc": args.max_nloc,
        "ccn": args.max_ccn,
        "nesting": args.max_nesting,
        "params": args.max_params,
    }
    try:
        results = [m for f in python_files(args.paths) for m in analyze_file(f)]
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    failures = sum(bool(exceeded(metrics, limits)) for metrics in results)
    shown = results if args.limit is None else results[: args.limit]
    if len(shown) < len(results):
        print(
            f"showing {len(shown)} of {len(results)} functions; raise --limit for more",
            file=sys.stderr,
        )
    if args.json:
        rows = [{**asdict(m), "exceeded": exceeded(m, limits)} for m in shown]
        print(json.dumps(rows, indent=2))
    else:
        print(f"{'nloc':>5} {'ccn':>4} {'nest':>4} {'par':>4}  location")
    for metrics in shown:
        problems = exceeded(metrics, limits)
        if not args.json:
            flag = "  !! " + ", ".join(problems) if problems else ""
            print(
                f"{metrics.nloc:>5} {metrics.ccn:>4} {metrics.nesting:>4} "
                f"{metrics.params:>4}  {metrics.path}:{metrics.line} "
                f"{metrics.name}{flag}"
            )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
