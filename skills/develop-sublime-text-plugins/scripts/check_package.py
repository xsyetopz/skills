"""Static checks for a Sublime Text package directory (no editor needed).

    python check_package.py PACKAGE_DIR [--external CMD ...] [--json]

Reports, one line each, and exits 1 when any is found:
- missing or unknown .python-version (selects the plugin host);
- a package name containing "." (Package Control: Python will not load);
- resource files (.sublime-commands/-keymap/-menu/-settings/-mousemap)
  that do not parse, allowing the comments and trailing commas Sublime
  accepts;
- "command" references with no command class in the package and not
  listed with --external (built-in or other-package commands);
- command class names with consecutive capitals (build 4213 changed how
  class names are snake-cased, so the command name depends on the build);
- commands with an input() method that no .sublime-commands entry lists
  (input handlers are shown only from the Command Palette);
- sublime.* calls at module level other than the import-time-safe ones
  (before build 4171 the API ignores them during import);
- __pycache__, *.pyc, package-metadata.json, or a root __init__.py.
"""

import argparse
import ast
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

HOST_VERSIONS = {"3.3", "3.8", "3.14"}
RESOURCES = (
    ".sublime-commands",
    ".sublime-keymap",
    ".sublime-menu",
    ".sublime-mousemap",
    ".sublime-settings",
)
COMMAND_FILES = (".sublime-commands", ".sublime-keymap", ".sublime-menu")
COMMAND_BASES = {"TextCommand", "WindowCommand", "ApplicationCommand"}
IMPORT_TIME_SAFE = {
    "version",
    "platform",
    "arch",
    "channel",
    "executable_path",
    "executable_hash",
    "packages_path",
    "installed_packages_path",
    "cache_path",
}
_TRAILING_COMMA = re.compile(r",(\s*[\]}])")
_ISSUE = re.compile(r"^([^:]+?)(?::(\d+))?: (.*)$", re.S)
EPILOG = """\
Exit status:
  0  no issues
  1  at least one issue
  2  PACKAGE_DIR is not a directory, or a plugin .py file does not parse

Output: one "FILE[:LINE]: message" line per issue, then "N issue(s) in
PACKAGE". --json prints {"package": NAME, "issues": [{file, line,
message}], "count": N}; line is null when the issue has none.

Examples:
  python3 scripts/check_package.py MyPackage
  python3 scripts/check_package.py MyPackage --external edit_settings \\
    --external show_panel
  python3 scripts/check_package.py MyPackage --json | jq '.issues'
"""


def strip_json_extensions(text: str) -> str:
    """Remove // and /* */ comments outside strings, then trailing commas."""
    out: list[str] = []
    i, n, in_string = 0, len(text), False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
            out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        else:
            out.append(c)
        i += 1
    return _TRAILING_COMMA.sub(r"\1", "".join(out))


def command_name(class_name: str) -> str:
    """Documented rule: drop "Command", split CamelCase, lower-case."""
    if class_name.endswith("Command"):
        class_name = class_name[: -len("Command")]
    return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _references(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        command = value.get("command")
        if isinstance(command, str):
            yield command
        for child in value.values():
            yield from _references(child)
    elif isinstance(value, list):
        for item in value:
            yield from _references(item)


def _module_level_calls(tree: ast.Module) -> Iterator[ast.Call]:
    """Calls executed at import: outside def bodies and lambdas."""
    stack: list[ast.AST] = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, ast.Call):
            yield node
        stack.extend(ast.iter_child_nodes(node))


def check(package: Path, external: set[str]) -> list[str]:
    issues: list[str] = []
    if "." in package.name:
        issues.append(f"{package.name}: package name contains '.'")
    marker = package / ".python-version"
    if not marker.is_file():
        issues.append(".python-version: missing; the host then differs by build")
    elif marker.read_text().strip() not in HOST_VERSIONS:
        issues.append(".python-version: expected one of 3.3, 3.8, 3.14")
    for path in sorted(package.rglob("*")):
        rel = path.relative_to(package).as_posix()
        if path.name == "__pycache__" or path.suffix == ".pyc":
            issues.append(f"{rel}: generated bytecode must not ship")
        elif path.name == "package-metadata.json":
            issues.append(f"{rel}: generated by Package Control on install")
    if (package / "__init__.py").exists():
        issues.append("__init__.py: packages must not have a root __init__.py")

    defined: dict[str, str] = {}
    with_input: set[str] = set()
    for source in sorted(package.glob("*.py")):
        tree = ast.parse(source.read_text(), str(source))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not COMMAND_BASES & {_base_name(b) for b in node.bases}:
                continue
            name = command_name(node.name)
            defined[name] = node.name
            if re.search(r"[A-Z]{2}", node.name):
                issues.append(
                    f"{source.name}: {node.name} has consecutive capitals; "
                    "its command name changed in build 4213"
                )
            if any(
                isinstance(item, ast.FunctionDef) and item.name == "input"
                for item in node.body
            ):
                with_input.add(name)
        for call in _module_level_calls(tree):
            func = call.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "sublime"
                and func.attr not in IMPORT_TIME_SAFE
                and func.attr[:1].islower()
            ):
                issues.append(
                    f"{source.name}:{call.lineno}: sublime.{func.attr}() at "
                    "import time; move it into plugin_loaded()"
                )

    palette: set[str] = set()
    for path in sorted(package.rglob("*")):
        if path.suffix not in RESOURCES:
            continue
        rel = path.relative_to(package).as_posix()
        try:
            data = json.loads(strip_json_extensions(path.read_text()))
        except ValueError as error:
            issues.append(f"{rel}: does not parse: {error}")
            continue
        if path.suffix not in COMMAND_FILES:
            continue
        for ref in _references(data):
            if path.suffix == ".sublime-commands":
                palette.add(ref)
            if ref not in defined and ref not in external:
                issues.append(f"{rel}: command '{ref}' is not defined")
    for name in sorted(with_input - palette):
        issues.append(
            f"{defined[name]}: input() needs a .sublime-commands entry for '{name}'"
        )
    return issues


def issue_record(issue: str) -> dict:
    """Split an issue line into {file, line, message}."""
    match = _ISSUE.match(issue)
    if not match:
        return {"file": None, "line": None, "message": issue}
    file, line, message = match.groups()
    return {"file": file, "line": int(line) if line else None, "message": message}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static checks for a Sublime Text package directory.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("package", type=Path, help="package directory")
    parser.add_argument(
        "--external",
        action="append",
        default=[],
        metavar="CMD",
        help="command defined outside the package (built-in or other package); "
        "repeatable",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    if not args.package.is_dir():
        print(
            f"error: {args.package} is not a directory; pass the package folder "
            "(the one holding the plugin .py files)",
            file=sys.stderr,
        )
        return 2
    try:
        issues = check(args.package, set(args.external))
    except SyntaxError as error:
        print(
            f"error: cannot parse {error.filename}:{error.lineno}: {error.msg}; "
            "fix the syntax error, then rerun",
            file=sys.stderr,
        )
        return 2
    if args.json:
        document = {
            "package": args.package.name,
            "issues": [issue_record(issue) for issue in issues],
            "count": len(issues),
        }
        print(json.dumps(document, indent=2))
        return 1 if issues else 0
    for issue in issues:
        print(issue)
    print(f"{len(issues)} issue(s) in {args.package.name}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
