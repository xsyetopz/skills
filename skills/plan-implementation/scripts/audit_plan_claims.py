#!/usr/bin/env python3
"""Check a plan's concrete claims against a repository.

Extracted claims:
  paths     `[files: a, b]` entries, and backticked tokens that contain
            "/" and end in a known extension (bare names like `settings.json`
            are usually runtime data, so they are not treated as claims)
  commands  `Verify: \\`cmd\\`` lines, lines in sh/bash/console fences, and
            backticked text starting with a known tool

Each path is reported once, at its first mention.

Checks (relative to REPO):
  - a path exists, or the plan marks it as new (the word "new", "create",
    or "add" appears before the path on a line that mentions it);
  - `just RECIPE` names a recipe in the justfile (`just --summary`);
  - `npm|pnpm|yarn|bun run SCRIPT` names a package.json script;
  - `make TARGET` names a target defined in the Makefile;
  - `python -m MODULE` resolves to a module file or package under REPO;
    for `python -m unittest|pytest`, dotted test names (tests.test_a or
    tests.test_a.Case.test_x) resolve to a module file under REPO, and
    `unittest discover` names a start directory (-s DIR) that exists;
  - otherwise the command's program is found on PATH or in REPO.

Usage: audit_plan_claims.py PLAN.md REPO [--json]
Exit status: 0 every claim checks out, 1 a claim is missing, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

EXTENSIONS = (
    ".c", ".cfg", ".cs", ".go", ".h", ".ini", ".java", ".js", ".json",
    ".just", ".kt", ".md", ".py", ".rb", ".rs", ".sh", ".sql", ".swift",
    ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
)  # fmt: skip
TOOLS = {
    "bun", "cargo", "dotnet", "go", "just", "make", "mvn", "node", "npm",
    "pnpm", "pytest", "python", "python3", "ruff", "uv", "yarn",
}  # fmt: skip
NEW_MARKERS = re.compile(r"\b(new|create|creates|add|adds)\b", re.IGNORECASE)
TEST_RUNNERS = {"unittest", "pytest"}
STDLIB_MODULES = {"unittest", "pytest", "compileall", "pip", "venv"}
# Options of unittest and pytest whose next argument is a value, not a test.
VALUE_OPTIONS = {"-c", "-k", "-m", "-p", "-s", "-t", "--pattern", "--rootdir"}
DOTTED = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+")
EPILOG = """\
Exit status:
  0  every claim checks out (or is marked new)
  1  at least one path or command is missing
  2  bad input: PLAN is unreadable or REPO is not a directory

Output: one line per claim, "STATUS   line N KIND: TEXT (detail)", where
STATUS is OK, MISSING, or UNKNOWN (could not check, e.g. just is not
installed). --json prints a list of {kind, text, line, status, detail}.

Examples:
  python3 scripts/audit_plan_claims.py PLAN.md .
  python3 scripts/audit_plan_claims.py --json PLAN.md ../repo \\
    | jq '.[] | select(.status == "missing")'
"""


@dataclass
class Claim:
    kind: str
    text: str
    line: int
    status: str
    detail: str = ""


def extract(text: str) -> list[tuple[str, str, int, str]]:
    """Return (kind, text, line number, full line) tuples."""
    found: list[tuple[str, str, int, str]] = []
    fence_lang = None
    for number, line in enumerate(text.splitlines(), 1):
        fence = re.match(r"^\s*```(\w*)", line)
        if fence:
            fence_lang = None if fence_lang is not None else fence.group(1).lower()
            continue
        if fence_lang is not None:
            command = line.strip().removeprefix("$ ")
            is_shell = fence_lang in {"sh", "bash", "console", "shell"}
            if is_shell and command and not command.startswith("#"):
                found.append(("command", command, number, line))
            continue
        files = re.search(r"\[files:\s*([^\]]+)\]", line)
        if files:
            for path in files.group(1).split(","):
                found.append(("path", path.strip(), number, line))
        verify = re.search(r"Verify:\s*`([^`]+)`", line)
        if verify:
            found.append(("command", verify.group(1), number, line))
        for span in re.findall(r"`([^`]+)`", line):
            if verify and span == verify.group(1):
                continue
            first = span.split(" ", 1)[0]
            if first in TOOLS:
                found.append(("command", span, number, line))
            elif " " not in span and "/" in span and span.endswith(EXTENSIONS):
                found.append(("path", span, number, line))
    return found


def just_recipes(repo: Path) -> set[str] | None:
    """Recipe names; empty set if there is no justfile; None if unknown."""
    if not any((repo / n).exists() for n in ("justfile", "Justfile", ".justfile")):
        return set()
    if not shutil.which("just"):
        return None
    result = subprocess.run(
        ["just", "--summary"], cwd=repo, capture_output=True, text=True, check=False
    )
    return set(result.stdout.split()) if result.returncode == 0 else None


def package_scripts(repo: Path) -> set[str] | None:
    manifest = repo / "package.json"
    if not manifest.exists():
        return None
    return set(json.loads(manifest.read_text()).get("scripts", {}))


def make_targets(repo: Path) -> set[str] | None:
    makefile = repo / "Makefile"
    if not makefile.exists():
        return None
    return set(re.findall(r"^([A-Za-z0-9_.-]+):", makefile.read_text(), re.M))


def check_command(command: str, repo: Path, cache: dict) -> tuple[str, str]:
    try:
        argv = shlex.split(command)
    except ValueError:
        return "unknown", "cannot parse"
    argv = [a for a in argv if "=" not in a or a.startswith("-")] or argv
    program = argv[0]
    rest = argv[1:]
    if program == "just" and rest:
        recipes = cache.setdefault("just", just_recipes(repo))
        recipe = next((a for a in rest if not a.startswith("-")), "")
        if recipes is None:
            return "unknown", "just not installed"
        ok = recipe in recipes
        return ("ok" if ok else "missing"), f"recipe '{recipe}'"
    if program in {"npm", "pnpm", "yarn", "bun"} and rest[:1] == ["run"]:
        try:
            scripts = cache.setdefault("pkg", package_scripts(repo))
        except (ValueError, AttributeError):
            return "unknown", "package.json is not a JSON object"
        name = rest[1] if len(rest) > 1 else ""
        if scripts is None:
            return "missing", "no package.json"
        return ("ok" if name in scripts else "missing"), f"script '{name}'"
    if program == "make" and rest:
        targets = cache.setdefault("make", make_targets(repo))
        if targets is None:
            return "missing", "no Makefile"
        return ("ok" if rest[0] in targets else "missing"), f"target '{rest[0]}'"
    if program.startswith("python") and rest[:1] == ["-m"] and len(rest) > 1:
        module = rest[1]
        if module in STDLIB_MODULES:
            start = discover_start(rest[2:]) if module == "unittest" else None
            if start is not None and not (repo / start).is_dir():
                return "missing", f"start directory {start}"
            if module in TEST_RUNNERS:
                for name in test_names(rest[2:]):
                    if not test_name_exists(repo, name):
                        return "missing", f"test module {name}"
            return "ok", f"stdlib module {module}"
        base = repo / module.replace(".", "/")
        exists = base.with_suffix(".py").exists() or (base / "__init__.py").exists()
        return ("ok" if exists else "missing"), f"module {module}"
    if program.startswith(("./", "../")) or "/" in program:
        return ("ok" if (repo / program).exists() else "missing"), program
    if program.startswith("python") and rest and rest[0].endswith(".py"):
        exists = (repo / rest[0]).exists()
        return ("ok" if exists else "missing"), f"script {rest[0]}"
    found = shutil.which(program) is not None
    return ("ok" if found else "missing"), f"program {program}"


def test_names(args: list[str]) -> list[str]:
    """Dotted test names and .py files among unittest or pytest arguments.

    `unittest discover` takes directories and a pattern, not test names,
    and option values (`-s tests`, `-t .`, `-k expr`) are not test names.
    """
    if args[:1] == ["discover"]:
        return []
    names: list[str] = []
    skip_value = False
    for arg in args:
        if skip_value:
            skip_value = False
        elif arg in VALUE_OPTIONS:
            skip_value = True
        elif arg.startswith("-") or "/" in arg or "::" in arg:
            continue
        elif arg.endswith(".py") or DOTTED.fullmatch(arg):
            names.append(arg)
    return names


def discover_start(args: list[str]) -> str | None:
    """The start directory of `unittest discover` (default "."), else None."""
    if args[:1] != ["discover"]:
        return None
    positional: list[str] = []
    rest = iter(args[1:])
    for arg in rest:
        if arg in {"-s", "--start-directory"}:
            return next(rest, ".")
        if arg in VALUE_OPTIONS:
            next(rest, None)
        elif not arg.startswith("-"):
            positional.append(arg)
    return positional[0] if positional else "."


def test_name_exists(repo: Path, name: str) -> bool:
    """A .py file, or a dotted name whose longest module prefix is a file.

    The parts after the module file are classes and methods, so
    tests.test_a.Case.test_x resolves when tests/test_a.py exists.
    """
    if name.endswith(".py"):
        return (repo / name).is_file()
    parts = name.split(".")
    for end in range(len(parts), 0, -1):
        base = repo.joinpath(*parts[:end])
        if base.with_suffix(".py").is_file():
            return True
        if end == len(parts) and base.is_dir():
            return True
    return False


def audit(plan_text: str, repo: Path) -> list[Claim]:
    claims: list[Claim] = []
    paths: dict[str, Claim] = {}
    cache: dict = {}
    for kind, text, number, line in extract(plan_text):
        if kind == "path":
            position = line.find(text)
            is_new = bool(NEW_MARKERS.search(line[: max(position, 0)]))
            claim = paths.get(text)
            if claim is None:
                claim = Claim(kind, text, number, "missing", "not in repo")
                if (repo / text).exists():
                    claim.status, claim.detail = "ok", ""
                paths[text] = claim
                claims.append(claim)
            if is_new and claim.status == "missing":
                claim.status, claim.detail = "ok", "marked new"
        else:
            status, detail = check_command(text, repo, cache)
            claims.append(Claim(kind, text, number, status, detail))
    return claims


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("plan", help="plan in Markdown (PLAN.md)")
    parser.add_argument("repo", help="repository root the claims refer to")
    parser.add_argument(
        "--json", action="store_true", help="print the claims as a JSON list"
    )
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    try:
        text = Path(args.plan).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read plan {args.plan}: {error}; "
            "expected a UTF-8 Markdown file",
            file=sys.stderr,
        )
        return 2
    if not repo.is_dir():
        print(
            f"error: REPO {repo} is not a directory; "
            "pass the repository root the plan refers to (for example .)",
            file=sys.stderr,
        )
        return 2
    claims = audit(text, repo)
    if args.json:
        print(json.dumps([asdict(c) for c in claims], indent=2))
    else:
        for claim in claims:
            detail = f" ({claim.detail})" if claim.detail else ""
            print(
                f"{claim.status.upper():8} line {claim.line} {claim.kind}: "
                f"{claim.text}{detail}"
            )
    return 1 if any(c.status == "missing" for c in claims) else 0


if __name__ == "__main__":
    raise SystemExit(main())
