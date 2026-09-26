#!/usr/bin/env python3
"""List compatibility-code candidates in Python sources.

Candidates (each needs consumer evidence before removal; this only finds
them):
  version-branch    `if sys.version_info <op> (X, Y)` and platform checks
                    on `sys.platform`
  import-fallback   `try: import A` / `except ImportError|ModuleNotFoundError`
  deprecated-alias  functions that call `warnings.warn(..., DeprecationWarning)`
                    or are decorated with `@deprecated` / `@warnings.deprecated`
  feature-probe     `hasattr(<module>, "name")` checks

With --min-python X.Y, version branches whose condition is always true or
always false for every supported version are marked `dead`.

Usage: find_compat_python.py PATH... [--min-python 3.11] [--json] [--limit N]
Exit status: 0 always when input is readable (candidates are not errors);
2 on unreadable input.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

EPILOG = """\
Exit status:
  0  scan finished (candidates are leads, not errors)
  2  bad usage: a PATH does not exist, a file does not parse or is not
     UTF-8, or --min-python is not MAJOR.MINOR

Output: one "PATH:LINE: KIND: DETAIL" line per candidate, then "N
candidate(s)" counting all. --json prints a list of candidates ({path,
line, kind, detail, ...}). --limit N prints at most N candidates and
notes the omission on stderr.

Examples:
  python3 scripts/find_compat_python.py src
  python3 scripts/find_compat_python.py src tests --min-python 3.11
  python3 scripts/find_compat_python.py src --json | jq 'map(.kind) | unique'
"""


def python_version(text: str) -> tuple[int, ...]:
    """Parse --min-python (3.11); argparse reports the error as usage."""
    parts = text.split(".")
    if not 1 <= len(parts) <= 2 or not all(part.isdigit() for part in parts):
        raise argparse.ArgumentTypeError(
            f"expected MAJOR.MINOR such as 3.11, got {text!r}"
        )
    return tuple(int(part) for part in parts)


@dataclass(frozen=True)
class Candidate:
    path: str
    line: int
    kind: str
    detail: str


def version_tuple(node: ast.expr) -> tuple[int, ...] | None:
    if isinstance(node, ast.Tuple) and all(
        isinstance(e, ast.Constant) and isinstance(e.value, int) for e in node.elts
    ):
        return tuple(e.value for e in node.elts)  # type: ignore[union-attr]
    return None


def is_sys_attr(node: ast.expr, name: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == name
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    )


def branch_status(test: ast.expr, min_version: tuple[int, ...] | None) -> str:
    if min_version is None or not isinstance(test, ast.Compare):
        return ""
    if len(test.ops) != 1 or not is_sys_attr(test.left, "version_info"):
        return ""
    bound = version_tuple(test.comparators[0])
    if bound is None:
        return ""
    op = test.ops[0]
    below = isinstance(op, (ast.Lt, ast.LtE))
    if below and min_version >= bound:
        return "dead: condition is false for every supported version"
    above = isinstance(op, (ast.GtE, ast.Gt))
    if above and min_version >= bound:
        return "dead: condition is true for every supported version"
    return "live for some supported versions"


def calls_deprecation_warning(function: ast.AST) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and any(
            isinstance(arg, ast.Name) and arg.id == "DeprecationWarning"
            for arg in [*node.args, *(k.value for k in node.keywords)]
        ):
            return True
    return False


def scan_file(path: Path, min_version: tuple[int, ...] | None) -> list[Candidate]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[Candidate] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            left = test.left if isinstance(test, ast.Compare) else None
            if left is not None and is_sys_attr(left, "version_info"):
                status = branch_status(test, min_version)
                found.append(
                    Candidate(
                        str(path),
                        node.lineno,
                        "version-branch",
                        f"{ast.unparse(test)} {status}".strip(),
                    )
                )
            elif left is not None and is_sys_attr(left, "platform"):
                found.append(
                    Candidate(
                        str(path), node.lineno, "version-branch", ast.unparse(test)
                    )
                )
        elif isinstance(node, ast.Try):
            imports = [
                n for n in node.body if isinstance(n, (ast.Import, ast.ImportFrom))
            ]
            caught = {ast.unparse(h.type) for h in node.handlers if h.type is not None}
            if imports and caught & {"ImportError", "ModuleNotFoundError"}:
                names = ", ".join(ast.unparse(i) for i in imports)
                found.append(
                    Candidate(str(path), node.lineno, "import-fallback", names)
                )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = {ast.unparse(d).split("(")[0] for d in node.decorator_list}
            if decorators & {
                "deprecated",
                "warnings.deprecated",
                "typing_extensions.deprecated",
            } or calls_deprecation_warning(node):
                found.append(
                    Candidate(str(path), node.lineno, "deprecated-alias", node.name)
                )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "hasattr" and len(node.args) == 2:
                target = node.args[0]
                if isinstance(target, ast.Name):
                    found.append(
                        Candidate(
                            str(path), node.lineno, "feature-probe", ast.unparse(node)
                        )
                    )
    return sorted(found, key=lambda c: (c.path, c.line))


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
    parser.add_argument(
        "--min-python",
        type=python_version,
        metavar="X.Y",
        help="oldest supported Python; marks always-true/false branches dead",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON list")
    parser.add_argument(
        "--limit", type=int, metavar="N", help="print at most N candidates"
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be 0 or more")
    minimum = args.min_python
    try:
        candidates = [
            c for f in python_files(args.paths) for c in scan_file(f, minimum)
        ]
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    shown = candidates if args.limit is None else candidates[: args.limit]
    if len(shown) < len(candidates):
        print(
            f"showing {len(shown)} of {len(candidates)} candidates; "
            "raise --limit for more",
            file=sys.stderr,
        )
    if args.json:
        print(json.dumps([asdict(c) for c in shown], indent=2))
    else:
        for c in shown:
            print(f"{c.path}:{c.line}: {c.kind}: {c.detail}")
        print(f"{len(candidates)} candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
