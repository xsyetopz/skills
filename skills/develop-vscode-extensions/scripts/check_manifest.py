"""Check a VS Code extension package.json against documented manifest rules.

Usage: check_manifest.py PACKAGE_JSON [--src DIR]... [--built] [--pre-release]
       [--json]

Prints one line per finding: ``<RULE> <error|warning>: <message>``.
Exit status: 0 no errors, 1 at least one error, 2 unreadable input.

Each rule cites its source in RULES. ``--src`` enables M015 (every
contributed command has a registerCommand call in the sources);
``--built`` enables M018 (``main``/``browser`` files exist).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DOCS = "https://code.visualstudio.com/api"
RULES: dict[str, str] = {
    "M001": f"{DOCS}/references/extension-manifest#fields",
    "M002": f"{DOCS}/references/extension-manifest#fields",
    "M003": f"{DOCS}/references/extension-manifest#fields",
    "M004": f"{DOCS}/working-with-extensions/publishing-extension"
    "#prerelease-extensions",
    "M005": f"{DOCS}/references/extension-manifest#fields",
    "M006": f"{DOCS}/working-with-extensions/publishing-extension"
    "#publishing-extensions",
    "M007": f"{DOCS}/references/extension-manifest#fields",
    "M008": f"{DOCS}/references/contribution-points#contributes.configuration",
    "M009": f"{DOCS}/references/contribution-points#contributes.configuration",
    "M010": f"{DOCS}/references/contribution-points#contributes.configuration",
    "M011": f"{DOCS}/extension-guides/workspace-trust#static-declarations",
    "M012": f"{DOCS}/extension-guides/workspace-trust#static-declarations",
    "M013": f"{DOCS}/extension-guides/virtual-workspaces",
    "M014": "https://github.com/microsoft/vscode/blob/main/src/vs/workbench/"
    "services/actions/common/menusExtensionPoint.ts",
    "M015": f"{DOCS}/extension-guides/command#registering-a-command",
    "M016": f"{DOCS}/references/activation-events#onCommand",
    "M017": f"{DOCS}/references/activation-events#Start-up",
    "M018": f"{DOCS}/references/extension-manifest#fields",
    "M019": f"{DOCS}/working-with-extensions/publishing-extension"
    "#prerelease-extensions",
    "M020": "https://github.com/microsoft/vscode-vsce/blob/main/src/validation.ts",
    "M021": f"{DOCS}/extension-guides/workspace-trust"
    "#what-if-i-dont-make-changes-to-my-extension",
}

CATEGORIES = {
    "Programming Languages",
    "Snippets",
    "Linters",
    "Themes",
    "Debuggers",
    "Formatters",
    "Keymaps",
    "SCM Providers",
    "Other",
    "Extension Packs",
    "Language Packs",
    "Data Science",
    "Machine Learning",
    "Visualization",
    "Notebooks",
    "Education",
    "Testing",
}
SCOPES = {
    "application",
    "machine",
    "machine-overridable",
    "window",
    "resource",
    "language-overridable",
}
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
ENGINE = re.compile(r"^[\^~>=]*\s*(\d+)\.(\d+)\.(\d+|x)")
EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  unreadable input: PACKAGE_JSON is missing or not a JSON object

Output: one "<RULE> <error|warning>: <message>" line per finding, then
"N error(s), N warning(s)". --json prints {"findings": [{rule, level,
message, source}], "errors": N, "warnings": N}; source is the rule's
documentation URL.

Examples:
  python3 scripts/check_manifest.py package.json --src src
  python3 scripts/check_manifest.py package.json --src src --built --pre-release
  python3 scripts/check_manifest.py package.json --json \\
    | jq '.findings[] | select(.level == "error")'
"""


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.findings: list[dict[str, str]] = []
        self.errors = 0

    def error(self, rule: str, message: str) -> None:
        self.errors += 1
        self.add(rule, "error", message)

    def warn(self, rule: str, message: str) -> None:
        self.add(rule, "warning", message)

    def add(self, rule: str, level: str, message: str) -> None:
        self.lines.append(f"{rule} {level}: {message}")
        self.findings.append(
            {"rule": rule, "level": level, "message": message, "source": RULES[rule]}
        )


def engine_floor(spec: str) -> tuple[int, int] | None:
    match = ENGINE.match(spec.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def check_identity(m: dict[str, Any], r: Report) -> None:
    for field in ("name", "version", "publisher"):
        if not isinstance(m.get(field), str) or not m[field]:
            r.error("M001", f"missing required field `{field}`")
    engines = m.get("engines")
    vscode = engines.get("vscode") if isinstance(engines, dict) else None
    if not isinstance(vscode, str):
        r.error("M001", "missing required field `engines.vscode`")
    elif vscode.strip() == "*":
        r.error("M002", "`engines.vscode` cannot be `*`")
    name = m.get("name")
    if isinstance(name, str) and (name != name.lower() or " " in name):
        r.error("M003", f"name `{name}` must be lowercase without spaces")
    version = m.get("version")
    if isinstance(version, str) and not VERSION.match(version):
        r.error(
            "M004",
            f"version `{version}`: Marketplace accepts major.minor.patch"
            " only; use --pre-release instead of a semver tag",
        )
    keywords = m.get("keywords", [])
    if isinstance(keywords, list) and len(keywords) > 30:
        r.error("M005", f"{len(keywords)} keywords; the limit is 30")
    icon = m.get("icon")
    if isinstance(icon, str) and icon.lower().endswith(".svg"):
        r.error("M006", f"icon `{icon}` is an SVG; use a PNG")
    for category in m.get("categories", []):
        if category not in CATEGORIES:
            r.error("M007", f"category `{category}` is not an allowed value")


def settings_of(contributes: dict[str, Any]) -> dict[str, dict[str, Any]]:
    config = contributes.get("configuration", [])
    blocks = config if isinstance(config, list) else [config]
    found: dict[str, dict[str, Any]] = {}
    for block in blocks:
        if isinstance(block, dict):
            found.update(block.get("properties", {}))
    return found


def check_configuration(contributes: dict[str, Any], r: Report) -> None:
    settings = settings_of(contributes)
    ids = sorted(settings)
    for a in ids:
        for b in ids:
            if a != b and b.startswith(a + "."):
                r.error("M008", f"setting `{a}` is a full prefix of `{b}`")
    for key, schema in settings.items():
        scope = schema.get("scope")
        if scope is not None and scope not in SCOPES:
            r.error("M009", f"setting `{key}` has unknown scope `{scope}`")
    if "$ref" in json.dumps(contributes.get("configuration", {})):
        r.error("M010", "`$ref` is not supported in configuration schemas")


def check_capabilities(m: dict[str, Any], r: Report) -> None:
    caps = m.get("capabilities", {})
    trust = caps.get("untrustedWorkspaces")
    settings = settings_of(m.get("contributes", {}))
    if trust is None and (m.get("main") or m.get("browser")):
        r.warn(
            "M021",
            "no capabilities.untrustedWorkspaces: the extension is disabled"
            " in Restricted Mode",
        )
    if trust is not None:
        supported = trust.get("supported") if isinstance(trust, dict) else None
        if supported not in (True, False, "limited"):
            r.error(
                "M011",
                "untrustedWorkspaces.supported must be true, false, or 'limited'",
            )
        elif supported is not True and not trust.get("description"):
            r.error(
                "M011",
                "untrustedWorkspaces needs a description when"
                " supported is false or 'limited'",
            )
        for key in trust.get("restrictedConfigurations", []) or []:
            if key not in settings:
                r.error(
                    "M012", f"restrictedConfigurations names undeclared setting `{key}`"
                )
    virtual = caps.get("virtualWorkspaces")
    if virtual is None or isinstance(virtual, bool):
        return
    if not isinstance(virtual, dict) or virtual.get("supported") not in (
        False,
        "limited",
    ):
        r.error(
            "M013",
            "virtualWorkspaces must be true, false, or"
            " {supported: false|'limited', description}",
        )
    elif not virtual.get("description"):
        r.error("M013", "virtualWorkspaces object needs a description")


def check_commands(m: dict[str, Any], sources: list[Path], r: Report) -> None:
    contributes = m.get("contributes", {})
    commands = [c.get("command") for c in contributes.get("commands", [])]
    declared = set(commands)
    for menu, items in contributes.get("menus", {}).items():
        for item in items:
            command = item.get("command")
            if command is not None and command not in declared:
                r.error(
                    "M014", f"menu `{menu}` references undeclared command `{command}`"
                )
    if sources:
        text = "\n".join(
            p.read_text(encoding="utf-8")
            for root in sources
            for p in sorted(root.rglob("*"))
            if p.suffix in {".ts", ".js", ".mts", ".cts", ".mjs", ".cjs"}
        )
        for command in commands:
            pattern = r"registerCommand\(\s*['\"`]" + re.escape(command)
            if not re.search(pattern, text):
                r.error(
                    "M015",
                    f"command `{command}` is contributed but"
                    " never passed to registerCommand",
                )
    events = m.get("activationEvents", [])
    if "*" in events:
        r.warn("M017", "`*` activates at startup; use a specific event")
    floor = engine_floor(m.get("engines", {}).get("vscode", "") or "")
    if floor is not None and floor < (1, 74):
        for command in commands:
            if f"onCommand:{command}" not in events:
                r.error(
                    "M016",
                    f"engines floor {floor[0]}.{floor[1]} < 1.74:"
                    f" add `onCommand:{command}` to activationEvents",
                )


def check_entries(m: dict[str, Any], root: Path, r: Report) -> None:
    for field in ("main", "browser"):
        entry = m.get(field)
        if not isinstance(entry, str):
            continue
        path = root / entry
        if not path.exists() and not path.with_suffix(".js").exists():
            r.error("M018", f"`{field}` points to missing file `{entry}`")


def check_tooling(m: dict[str, Any], pre_release: bool, r: Report) -> None:
    floor = engine_floor(m.get("engines", {}).get("vscode", "") or "")
    if floor is None:
        return
    if pre_release and floor < (1, 63):
        r.error("M019", "pre-release packages need engines.vscode >= 1.63")
    types = m.get("devDependencies", {}).get("@types/vscode")
    types_floor = engine_floor(types) if isinstance(types, str) else None
    if types_floor is not None and types_floor > floor:
        r.error(
            "M020",
            f"@types/vscode {types} is newer than the engines"
            f" floor {floor[0]}.{floor[1]}; APIs past the floor"
            " type-check but fail on older hosts",
        )


def check(
    manifest: Path, sources: list[Path], built: bool, pre_release: bool
) -> Report:
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(m, dict):
        raise ValueError("package.json is not a JSON object")
    r = Report()
    check_identity(m, r)
    check_configuration(m.get("contributes", {}), r)
    check_capabilities(m, r)
    check_commands(m, sources, r)
    if built:
        check_entries(m, manifest.parent, r)
    check_tooling(m, pre_release, r)
    return r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a VS Code package.json.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("manifest", type=Path, help="the extension's package.json")
    parser.add_argument(
        "--src",
        type=Path,
        action="append",
        default=[],
        help="source directory to search for registerCommand (M015); repeatable",
    )
    parser.add_argument(
        "--built",
        action="store_true",
        help="check that main/browser files exist (M018)",
    )
    parser.add_argument(
        "--pre-release",
        action="store_true",
        help="apply pre-release rules (M019: engines.vscode >= 1.63)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        report = check(args.manifest, args.src, args.built, args.pre_release)
    except (OSError, ValueError, AttributeError) as error:
        print(
            f"cannot check {args.manifest}: {error}; "
            "expected a readable package.json holding a JSON object",
            file=sys.stderr,
        )
        return 2
    if args.json:
        warnings = len(report.findings) - report.errors
        document = {
            "findings": report.findings,
            "errors": report.errors,
            "warnings": warnings,
        }
        print(json.dumps(document, indent=2))
        return 1 if report.errors else 0
    for line in report.lines:
        print(line)
    print(f"{report.errors} error(s), {len(report.lines) - report.errors} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
