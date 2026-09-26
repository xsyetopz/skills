#!/usr/bin/env python3
"""Find Python code that hides errors, guesses defaults, or blurs namespaces.

Kinds reported (each is a candidate for review, not a verdict):
  silenced-except  an except handler whose body is only pass, ..., or
                   continue: the error disappears without a trace
  broad-except     `except:`, `except Exception`, or `except BaseException`
                   whose body does not re-raise
  wide-suppress    `with suppress(...)` around more than one statement, so
                   the expected error can come from an unexpected line
  or-default       `param or default` inside a function: 0, "", False, and
                   empty containers are replaced as if they were missing
  star-import      `from module import *`: names arrive without a namespace
                   and can shadow builtins or each other

Usage: zen_scan.py PATH... [--json] [--limit N]
Exit status: 0 no findings, 1 findings, 2 unreadable or unparsable input.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

BROAD = {"Exception", "BaseException"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    detail: str


def is_silent(body: list[ast.stmt]) -> bool:
    for statement in body:
        if isinstance(statement, (ast.Pass, ast.Continue)):
            continue
        if isinstance(statement, ast.Expr) and isinstance(
            statement.value, ast.Constant
        ):
            continue  # `...` or a docstring-like string
        return False
    return True


def reraises(body: list[ast.stmt]) -> bool:
    return any(isinstance(node, ast.Raise) for s in body for node in ast.walk(s))


def is_suppress(expr: ast.expr) -> bool:
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    return name == "suppress"


def parameters(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = function.args
    every = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    every += [a for a in (args.vararg, args.kwarg) if a is not None]
    return {a.arg for a in every}


class Scanner(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.findings: list[Finding] = []
        self.params: list[set[str]] = []

    def add(self, node: ast.AST, kind: str, detail: str) -> None:
        line = getattr(node, "lineno", 0)
        self.findings.append(Finding(self.path, line, kind, detail))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.params.append(parameters(node))
        self.generic_visit(node)
        self.params.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.params.append(parameters(node))
        self.generic_visit(node)
        self.params.pop()

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        caught = "everything" if node.type is None else ast.unparse(node.type)
        if is_silent(node.body):
            self.add(node, "silenced-except", f"except {caught}: no action")
        elif (node.type is None or caught in BROAD) and not reraises(node.body):
            self.add(node, "broad-except", f"except {caught} without re-raise")
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        if any(is_suppress(i.context_expr) for i in node.items) and len(node.body) > 1:
            self.add(node, "wide-suppress", f"{len(node.body)} statements")
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        first = node.values[0]
        if (
            isinstance(node.op, ast.Or)
            and self.params
            and isinstance(first, ast.Name)
            and first.id in self.params[-1]
        ):
            self.add(node, "or-default", ast.unparse(node))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if any(alias.name == "*" for alias in node.names):
            self.add(node, "star-import", f"from {node.module} import *")


EPILOG = """\
Exit status:
  0  no findings
  1  at least one finding
  2  a PATH does not exist, or a file does not parse or is not UTF-8

Output: one "PATH:LINE: KIND: DETAIL" line per finding, then "N
finding(s)" counting all. --json prints a list of {path, line, kind,
detail}. --limit N prints at most N findings (the count and exit status
still cover all) and notes the omission on stderr.

Examples:
  python3 scripts/zen_scan.py src
  python3 scripts/zen_scan.py src --limit 40
  python3 scripts/zen_scan.py src --json | jq 'group_by(.kind) | map(length)'
"""


def scan(path: Path) -> list[Finding]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    scanner = Scanner(str(path))
    scanner.visit(tree)
    return sorted(scanner.findings, key=lambda f: f.line)


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="Python files or directories")
    parser.add_argument("--json", action="store_true", help="print a JSON list")
    parser.add_argument(
        "--limit", type=int, metavar="N", help="print at most N findings"
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be 0 or more")
    try:
        findings = [f for p in python_files(args.paths) for f in scan(p)]
    except (OSError, SyntaxError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    shown = findings if args.limit is None else findings[: args.limit]
    if len(shown) < len(findings):
        print(
            f"showing {len(shown)} of {len(findings)} findings; raise --limit for more",
            file=sys.stderr,
        )
    if args.json:
        print(json.dumps([asdict(f) for f in shown], indent=2))
    else:
        for f in shown:
            print(f"{f.path}:{f.line}: {f.kind}: {f.detail}")
        print(f"{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
