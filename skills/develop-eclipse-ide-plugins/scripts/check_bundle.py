#!/usr/bin/env python3
"""Check an Eclipse plug-in project directory for structural mistakes.

Usage:
    check_bundle.py [--json] BUNDLE_DIR [BUNDLE_DIR ...]

A bundle directory holds META-INF/MANIFEST.MF, build.properties, and
optionally plugin.xml. Rules and their sources:

MANIFEST.MF (JAR File Specification "Manifest Specification"; OSGi Core
8 section 3.2; PDE pderesources.properties):
  M001 a line is longer than 72 bytes in UTF-8 (JAR spec)
  M002 the file does not end with a newline: java.util.jar.Manifest drops
       the last header (Equinox keeps it)
  M003 a line is neither "Name: value" nor a continuation starting with
       one space
  M004 a continuation starts with two or more spaces: the extra spaces
       become part of the value (warning)
  M005 a blank line inside the main section ends it early
  M006 Bundle-ManifestVersion is not 2
  M007 Bundle-SymbolicName is missing
  M008 Bundle-Version is not major[.minor[.micro[.qualifier]]]
  M009 plugin.xml declares extensions or extension points, but
       Bundle-SymbolicName lacks singleton:=true (PDE error)
  M010 Bundle-RequiredExecutionEnvironment and an osgi.ee
       Require-Capability are both set (OSGi: use one; warning)

build.properties (PDE build configuration; PDE BuildErrorReporter):
  B001 bin.includes is missing
  B002 bin.includes lacks META-INF/
  B003 plugin.xml exists but bin.includes lacks it
  B004 a source.. entry exists but bin.includes lacks "."
  B005 a comma-terminated value has no backslash, so the next line
       starts a new property and the list is cut short
  B006 Java sources exist but there is no source.. entry
  B007 a file referenced by an icon attribute in plugin.xml is not
       covered by bin.includes

plugin.xml (Platform Plug-in Developer Guide, commands and menus):
  X001 plugin.xml is not well-formed XML
  X002 a handler, menu, key binding, or command reference names a command
       that is not declared here; an error for ids in the bundle's own
       namespace, a warning for others outside org.eclipse.*
  X003 a menuContribution locationURI does not start with menu:, popup:,
       or toolbar:
  X004 a <reference definitionId> in the bundle's namespace has no
       <definition> in org.eclipse.core.expressions.definitions
  X005 a class attribute in the bundle's namespace has no source file
       under the source.. folders
  X006 two commands, views, or definitions share an id
  X007 a marker <super type> in the bundle's namespace is not declared

Exit status: 0 without errors, 1 with errors, 2 on usage errors (a
BUNDLE_DIR that is not a directory, or an unreadable file).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

VERSION = re.compile(r"^\d+(\.\d+(\.\d+(\.[A-Za-z0-9_-]+)?)?)?$")
HEADER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*: ")
LOCATION_SCHEMES = ("menu:", "popup:", "toolbar:")
COMMAND_REF_TAGS = ("handler", "command", "key")
EPILOG = """\
Output: "ERROR PATH: [RULE] ..." lines, then "WARN PATH: [RULE] ..."
lines, then "N error(s), N warning(s)". --json prints {"findings":
[{level, file, rule, message}], "errors": N, "warnings": N}.

Examples:
  python3 scripts/check_bundle.py plugins/org.acme.todos
  python3 scripts/check_bundle.py plugins/org.acme.todos plugins/org.acme.todos.ui
  python3 scripts/check_bundle.py --json plugins/* | jq '.findings[].rule'
"""


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    findings: list[dict[str, str]] = field(default_factory=list)

    def error(self, where: Path, rule: str, message: str) -> None:
        self.errors.append(f"ERROR {where}: [{rule}] {message}")
        self.record("error", where, rule, message)

    def warn(self, where: Path, rule: str, message: str) -> None:
        self.warnings.append(f"WARN {where}: [{rule}] {message}")
        self.record("warning", where, rule, message)

    def record(self, level: str, where: Path, rule: str, message: str) -> None:
        self.findings.append(
            {"level": level, "file": str(where), "rule": rule, "message": message}
        )


def read_manifest(path: Path, report: Report) -> dict[str, str]:
    """Parse the main section and apply the line rules."""
    data = path.read_bytes()
    if data and not data.endswith((b"\n", b"\r")):
        report.error(
            path,
            "M002",
            "no newline after the last line; java.util.jar.Manifest drops that header",
        )
    headers: dict[str, str] = {}
    current: str | None = None
    lines = data.decode("utf-8").splitlines()
    for number, line in enumerate(lines, 1):
        size = len(line.encode("utf-8"))
        if size > 72:
            report.error(path, "M001", f"line {number} is {size} bytes (max 72)")
        if not line:
            rest = [x for x in lines[number:] if x]
            if rest:
                report.error(
                    path,
                    "M005",
                    f"blank line {number} ends the main section;"
                    f" {len(rest)} later line(s) leave it",
                )
            break
        if line.startswith(" "):
            if current is None:
                report.error(path, "M003", f"line {number} continues nothing")
                continue
            if line.startswith("  "):
                report.warn(
                    path,
                    "M004",
                    f"line {number} starts with more than one space;"
                    " the rest become part of the value",
                )
            headers[current] += line[1:]
            continue
        if not HEADER.match(line):
            report.error(
                path,
                "M003",
                f"line {number} is not 'Name: value' and does not start with a space",
            )
            current = None
            continue
        name, value = line.split(": ", 1)
        headers[name] = value
        current = name
    return headers


def symbolic_name(headers: dict[str, str]) -> tuple[str, bool]:
    raw = headers.get("Bundle-SymbolicName", "")
    parts = [p.strip() for p in raw.split(";")]
    singleton = any(re.fullmatch(r"singleton:=\s*\"?true\"?", p) for p in parts[1:])
    return parts[0], singleton


def check_manifest(
    bundle: Path, headers: dict[str, str], has_extensions: bool, report: Report
) -> None:
    where = bundle / "META-INF/MANIFEST.MF"
    if headers.get("Bundle-ManifestVersion") != "2":
        report.error(where, "M006", "Bundle-ManifestVersion must be 2")
    name, singleton = symbolic_name(headers)
    if not name:
        report.error(where, "M007", "Bundle-SymbolicName is missing")
    version = headers.get("Bundle-Version", "0.0.0").strip()
    if not VERSION.match(version):
        report.error(where, "M008", f"Bundle-Version {version!r} is not valid")
    if has_extensions and not singleton:
        report.error(
            where,
            "M009",
            "Plug-ins declaring extensions or extension points must set"
            " the 'singleton' directive to 'true'",
        )
    if "Bundle-RequiredExecutionEnvironment" in headers and "osgi.ee" in (
        headers.get("Require-Capability", "")
    ):
        report.warn(
            where,
            "M010",
            "both Bundle-RequiredExecutionEnvironment and an osgi.ee"
            " requirement are set; both must resolve",
        )


def read_properties(path: Path, report: Report) -> dict[str, str]:
    """Java .properties logical lines, with the B005 cut-list check."""
    props: dict[str, str] = {}
    pending = ""
    previous_key = None
    for number, raw in enumerate(path.read_text("utf-8").splitlines(), 1):
        line = raw.strip() if not pending else raw.lstrip()
        if not pending and (not line or line[0] in "#!"):
            continue
        if line.endswith("\\") and not line.endswith("\\\\"):
            pending += line[:-1]
            continue
        logical = pending + line
        pending = ""
        match = re.match(r"([^=:\s]+)\s*[=:]?\s*(.*)$", logical)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if (
            previous_key
            and props[previous_key].endswith(",")
            and (not match.group(2) or key.startswith((".", "/")))
        ):
            report.error(
                path,
                "B005",
                f"line {number}: {previous_key} ends with ',' but the line"
                " has no '\\'; this line became a separate property",
            )
        props[key] = value
        previous_key = key
    if pending:
        match = re.match(r"([^=:\s]+)\s*[=:]?\s*(.*)$", pending)
        if match:
            props[match.group(1)] = match.group(2).strip()
    return props


def split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def covered(entry: str, includes: list[str]) -> bool:
    for include in includes:
        if include == entry:
            return True
        if include.endswith("/") and entry.startswith(include):
            return True
    return False


def check_build_properties(
    bundle: Path, props: dict[str, str], icons: set[str], report: Report
) -> None:
    where = bundle / "build.properties"
    if "bin.includes" not in props:
        report.error(where, "B001", "bin.includes is missing")
        return
    includes = split_list(props["bin.includes"])
    if "META-INF/" not in includes:
        report.error(where, "B002", "bin.includes lacks META-INF/")
    if (bundle / "plugin.xml").exists() and "plugin.xml" not in includes:
        report.error(where, "B003", "bin.includes lacks plugin.xml")
    if "source.." in props and "." not in includes:
        report.error(where, "B004", "source.. is set but bin.includes lacks '.'")
    if "source.." not in props and any(bundle.rglob("*.java")):
        report.error(where, "B006", "Java sources exist but source.. is missing")
    for icon in sorted(icons):
        if not covered(icon, includes):
            report.error(where, "B007", f"icon {icon} is not covered by bin.includes")


def plugin_ids(root: ET.Element, point: str, tag: str) -> list[str]:
    ids = []
    for ext in root.iter("extension"):
        if ext.get("point") == point:
            ids.extend(e.get("id", "") for e in ext.iter(tag))
    return [i for i in ids if i]


def check_plugin_xml(
    bundle: Path,
    root: ET.Element,
    name: str,
    source_dirs: list[Path],
    report: Report,
) -> None:
    where = bundle / "plugin.xml"
    own = name + "."
    commands = plugin_ids(root, "org.eclipse.ui.commands", "command")
    views = plugin_ids(root, "org.eclipse.ui.views", "view")
    definitions = plugin_ids(
        root, "org.eclipse.core.expressions.definitions", "definition"
    )
    for kind, ids in (
        ("command", commands),
        ("view", views),
        ("definition", definitions),
    ):
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            report.error(where, "X006", f"{kind} id {dup} is declared twice")
    declared = set(commands)
    for ext in root.iter("extension"):
        point = ext.get("point", "")
        if point == "org.eclipse.ui.commands":
            continue
        for element in ext.iter():
            if element.tag not in COMMAND_REF_TAGS:
                continue
            ref = element.get("commandId")
            if not ref or ref in declared or ref.startswith("org.eclipse."):
                continue
            message = f"<{element.tag}> names undeclared command {ref}"
            if ref.startswith(own):
                report.error(where, "X002", message)
            else:
                report.warn(where, "X002", message)
        for contribution in ext.iter("menuContribution"):
            uri = contribution.get("locationURI", "")
            if not uri.startswith(LOCATION_SCHEMES):
                report.error(
                    where,
                    "X003",
                    f"locationURI {uri!r} must start with menu:, popup:, or toolbar:",
                )
    for reference in root.iter("reference"):
        ref = reference.get("definitionId", "")
        if ref.startswith(own) and ref not in definitions:
            report.error(where, "X004", f"definition {ref} is not declared")
    marker_ids = {
        f"{name}.{ext.get('id')}"
        for ext in root.iter("extension")
        if ext.get("point") == "org.eclipse.core.resources.markers" and ext.get("id")
    }
    for ext in root.iter("extension"):
        if ext.get("point") != "org.eclipse.core.resources.markers":
            continue
        for sup in ext.iter("super"):
            parent = sup.get("type", "")
            if parent.startswith(own) and parent not in marker_ids:
                report.error(where, "X007", f"marker super type {parent} is undeclared")
    for element in root.iter():
        value = element.get("class", "")
        cls = value.split(":", 1)[0]
        if not cls.startswith(own) or not source_dirs:
            continue
        relative = Path(*cls.split(".")).with_suffix(".java")
        if not any((src / relative).exists() for src in source_dirs):
            report.error(where, "X005", f"class {cls} has no source file {relative}")


def check_bundle(bundle: Path, report: Report) -> None:
    manifest = bundle / "META-INF/MANIFEST.MF"
    if not manifest.is_file():
        report.error(bundle, "M007", "META-INF/MANIFEST.MF is missing")
        return
    headers = read_manifest(manifest, report)
    name, _ = symbolic_name(headers)
    root = None
    plugin = bundle / "plugin.xml"
    if plugin.exists():
        try:
            root = ET.parse(plugin).getroot()
        except ET.ParseError as error:
            report.error(plugin, "X001", str(error))
    has_extensions = root is not None and (
        root.find("extension") is not None or root.find("extension-point") is not None
    )
    check_manifest(bundle, headers, has_extensions, report)
    props_path = bundle / "build.properties"
    props = read_properties(props_path, report) if props_path.exists() else {}
    if not props_path.exists():
        report.error(bundle, "B001", "build.properties is missing")
    icons = set()
    if root is not None:
        icons = {e.get("icon", "") for e in root.iter() if e.get("icon")}
    if props:
        check_build_properties(bundle, props, icons, report)
    sources = [bundle / s for s in split_list(props.get("source..", ""))]
    if root is not None and name:
        check_plugin_xml(bundle, root, name, sources, report)


def usage() -> str:
    return "usage: check_bundle.py [--json] BUNDLE_DIR [BUNDLE_DIR ...]"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        usage=usage().removeprefix("usage: "),
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "bundles", nargs="+", metavar="BUNDLE_DIR", help="plug-in project directory"
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit:  # keep main() returning a status for callers
        return int(exit.code or 0)
    report = Report()
    for arg in args.bundles:
        bundle = Path(arg)
        if not bundle.is_dir():
            print(
                f"not a directory: {arg}; pass a plug-in project directory "
                "holding META-INF/MANIFEST.MF",
                file=sys.stderr,
            )
            return 2
        try:
            check_bundle(bundle, report)
        except (OSError, UnicodeDecodeError) as error:
            print(f"cannot read {bundle}: {error}", file=sys.stderr)
            return 2
    if args.json:
        document = {
            "findings": report.findings,
            "errors": len(report.errors),
            "warnings": len(report.warnings),
        }
        print(json.dumps(document, indent=2))
        return 1 if report.errors else 0
    for line in report.errors + report.warnings:
        print(line)
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
