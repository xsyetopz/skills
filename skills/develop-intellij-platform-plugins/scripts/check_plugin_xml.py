#!/usr/bin/env python3
"""Check an IntelliJ Platform plugin.xml for structural mistakes.

Usage:
    check_plugin_xml.py [--patched] [--config-dir DIR] [--src-root DIR ...]
        [--json] plugin.xml

Checks (rules from plugins.jetbrains.com/docs/intellij/
plugin-configuration-file.html and build-number-ranges.html):

- required elements: <name> and <vendor>; <id>, <version>, <idea-version>,
  and <description> are errors only with --patched (a source descriptor may
  leave them to the Gradle patchPluginXml task);
- plugin id: no prefix or word that JetBrains Plugin Verifier rejects
  (ForbiddenPluginIdPrefix, TemplateWordInPluginId in intellij-plugin-
  verifier PluginIdVerifier.kt), at most 255 characters, one line;
- since-build/until-build/strict-until-build format and order;
- <depends optional="true"> has a config-file that exists and is named
  <pluginId>-<name>.xml (looked up next to the descriptor, or in
  --config-dir for a patched copy); optional config files are checked too;
- own extension points: name/qualifiedName and interface/beanClass are
  exclusive; non-dynamic points are reported; extensions in the plugin's
  own namespace use a declared point, and interface points get an
  `implementation` attribute;
- actions and groups: ids present and unique, groups have ids, actions
  have `class` and `text` unless a resource bundle is declared;
- with --src-root, every registered class name in a package the sources
  own (its first two segments exist as directories under a source root)
  resolves to a Kotlin or Java source file declaring that class; names in
  other packages (platform, other plugins, libraries) are not checked.

Exit status: 0 without errors, 1 with errors, 2 on usage or parse errors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

BUILD = re.compile(r"^\d{3}(\.\d+)*$")
UNTIL = re.compile(r"^\d{3}(\.\d+)*(\.\*)?$")
CLASS_ATTRS = (
    "class",
    "implementation",
    "instance",
    "provider",
    "serviceInterface",
    "serviceImplementation",
    "testServiceImplementation",
    "headlessImplementation",
    "implementationClass",
    "factoryClass",
    "interface",
    "beanClass",
)
PATCHABLE = ("id", "version", "idea-version", "description")
# intellij-plugin-verifier: structure-intellij/.../verifiers/PluginIdVerifier.kt
FORBIDDEN_ID_PREFIXES = (
    "com.example",
    "net.example",
    "org.example",
    "edu.example",
    "com.intellij",
    "org.jetbrains",
)
RESTRICTED_ID_WORDS = frozenset(
    [
        "aqua",
        "clion",
        "datagrip",
        "datalore",
        "dataspell",
        "dotcover",
        "dotmemory",
        "dotpeek",
        "dottrace",
        "fleet",
        "goland",
        "intellij",
        "qodana",
        "phpstorm",
        "pycharm",
        "resharper",
        "rider",
        "rubymine",
        "space",
        "webstorm",
        "youtrack",
    ]
)


EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  usage error, or a descriptor is missing or is not well-formed XML

Output: "ERROR FILE: ..." lines, then "WARN FILE: ..." lines, then
"checked N descriptor(s): N error(s), N warning(s)". --json prints
{"findings": [{level, file, message}], "errors": N, "warnings": N,
"descriptors": N}; level is "error" or "warning".

Examples:
  python3 scripts/check_plugin_xml.py src/main/resources/META-INF/plugin.xml
  python3 scripts/check_plugin_xml.py --src-root src/main/kotlin \\
    src/main/resources/META-INF/plugin.xml
  python3 scripts/check_plugin_xml.py --patched \\
    build/tmp/patchPluginXml/plugin.xml --config-dir src/main/resources/META-INF
  python3 scripts/check_plugin_xml.py --json plugin.xml | jq '.findings'
"""


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    findings: list[dict[str, str]] = field(default_factory=list)

    def error(self, where: Path, message: str) -> None:
        self.errors.append(f"ERROR {where}: {message}")
        self.findings.append({"level": "error", "file": str(where), "message": message})

    def warn(self, where: Path, message: str) -> None:
        self.warnings.append(f"WARN {where}: {message}")
        self.findings.append(
            {"level": "warning", "file": str(where), "message": message}
        )


@dataclass
class ExtensionPoint:
    name: str
    is_interface: bool
    dynamic: bool


def build_key(value: str) -> tuple[int, ...]:
    parts = value.removesuffix(".*").split(".")
    return tuple(int(p) for p in parts)


def check_versions(root: ET.Element, path: Path, report: Report) -> None:
    version = root.find("idea-version")
    if version is None:
        return
    since = version.get("since-build")
    if since is None:
        report.error(path, "<idea-version> without since-build")
    elif not BUILD.match(since):
        report.error(path, f"since-build {since!r} is not a build number")
    for attr in ("until-build", "strict-until-build"):
        until = version.get(attr)
        if until is None:
            continue
        if not UNTIL.match(until):
            report.error(path, f"{attr} {until!r} is not a build number")
        elif (
            since
            and BUILD.match(since)
            and build_key(until)[: len(build_key(since))] < build_key(since)
        ):
            report.error(path, f"{attr} {until} is before {since}")


def check_required(root: ET.Element, path: Path, patched: bool, report: Report) -> None:
    for tag in ("name", "vendor"):
        if root.find(tag) is None:
            report.error(path, f"missing required <{tag}>")
    for tag in PATCHABLE:
        if root.find(tag) is None:
            message = f"missing <{tag}>"
            if patched:
                report.error(path, message)
            else:
                report.warn(path, message + " (must come from patchPluginXml)")
    if root.find("depends") is None:
        report.warn(
            path,
            "no <depends>; platform-only plugins declare com.intellij.modules.platform",
        )


def check_id(plugin_id: str, path: Path, report: Report) -> None:
    for prefix in FORBIDDEN_ID_PREFIXES:
        if plugin_id.startswith(prefix):
            report.error(path, f"plugin id prefix {prefix!r} is rejected")
    for word in plugin_id.split("."):
        if word.lower() in RESTRICTED_ID_WORDS:
            report.error(path, f"plugin id contains product word {word!r}")
    if len(plugin_id) > 255 or "\n" in plugin_id:
        report.error(path, "plugin id is longer than 255 or multi-line")


def optional_configs(
    root: ET.Element,
    path: Path,
    plugin_id: str | None,
    config_dir: Path | None,
    report: Report,
) -> list[Path]:
    configs: list[Path] = []
    for dep in root.findall("depends"):
        target = (dep.text or "").strip()
        config = dep.get("config-file")
        if dep.get("optional") == "true" and not config:
            report.error(path, f"optional depends {target} has no config-file")
        if not config:
            continue
        config_path = (config_dir or path.parent) / config
        if not config_path.is_file():
            report.error(path, f"config-file {config} does not exist")
            continue
        if plugin_id and not config.startswith(plugin_id + "-"):
            report.warn(
                path, f"config-file {config} should be named {plugin_id}-<name>.xml"
            )
        configs.append(config_path)
    return configs


def declared_points(
    root: ET.Element, path: Path, plugin_id: str | None, report: Report
) -> dict[str, ExtensionPoint]:
    points: dict[str, ExtensionPoint] = {}
    for ep in root.iter("extensionPoint"):
        name, qualified = ep.get("name"), ep.get("qualifiedName")
        if (name is None) == (qualified is None):
            report.error(path, "extensionPoint needs exactly one of name/qualifiedName")
            continue
        iface, bean = ep.get("interface"), ep.get("beanClass")
        if (iface is None) == (bean is None):
            report.error(
                path,
                f"extensionPoint {name or qualified} needs "
                "exactly one of interface/beanClass",
            )
        full = qualified or f"{plugin_id}.{name}"
        if full in points:
            report.error(path, f"extensionPoint {full} declared twice")
        dynamic = ep.get("dynamic") == "true"
        if not dynamic:
            report.warn(path, f'extensionPoint {full} is not dynamic="true"')
        points[full] = ExtensionPoint(full, iface is not None, dynamic)
    return points


def check_extensions(
    root: ET.Element,
    path: Path,
    plugin_id: str | None,
    points: dict[str, ExtensionPoint],
    report: Report,
) -> None:
    for block in root.findall("extensions"):
        namespace = block.get("defaultExtensionNs")
        for ext in block:
            full = f"{namespace}.{ext.tag}" if namespace else ext.tag
            if plugin_id is None or not full.startswith(plugin_id + "."):
                continue
            point = points.get(full)
            if point is None:
                report.error(
                    path, f"<{ext.tag}> uses undeclared extension point {full}"
                )
            elif point.is_interface and not ext.get("implementation"):
                report.error(
                    path,
                    f"<{ext.tag}> for interface point {full} "
                    "has no implementation attribute",
                )


def check_actions(
    root: ET.Element, path: Path, report: Report, seen: dict[str, Path]
) -> None:
    bundled = root.find("resource-bundle") is not None
    for actions in root.findall("actions"):
        has_bundle = bundled or actions.get("resource-bundle") is not None
        for node in actions.iter():
            if node.tag not in ("action", "group"):
                continue
            ident = node.get("id")
            if node.tag == "group" and ident is None:
                report.error(path, "<group> without id (dynamic plugins require one)")
            if node.tag == "action":
                if node.get("class") is None:
                    report.error(path, f"action {ident} has no class")
                if ident is None:
                    report.warn(
                        path, "action without id defaults to the class short name"
                    )
                    ident = (node.get("class") or "").rsplit(".", 1)[-1]
                if node.get("text") is None and not has_bundle:
                    report.error(
                        path, f"action {ident} has no text and no resource bundle"
                    )
            if ident:
                if ident in seen:
                    report.error(path, f"duplicate action/group id {ident}")
                seen[ident] = path


def class_names(root: ET.Element) -> set[str]:
    names: set[str] = set()
    for node in root.iter():
        for attr in CLASS_ATTRS:
            value = node.get(attr)
            if value and re.fullmatch(r"[\w$]+(\.[\w$]+)+", value):
                names.add(value)
    return names


def owned(fqn: str, src_roots: list[Path]) -> bool:
    top = fqn.split(".")[:2]
    return any(src.joinpath(*top).is_dir() for src in src_roots)


def resolves(fqn: str, src_roots: list[Path]) -> bool:
    package, _, simple = fqn.rpartition(".")
    outer = simple.split("$", 1)[0]
    declaration = re.compile(
        rf"\b(class|interface|object|enum|record)\s+{re.escape(outer)}\b"
    )
    package_line = re.compile(
        rf"^\s*package\s+{re.escape(package)}\s*;?\s*$", re.MULTILINE
    )
    for src in src_roots:
        directory = src.joinpath(*package.split("."))
        if not directory.is_dir():
            continue
        for source in directory.iterdir():
            if source.suffix not in (".kt", ".java"):
                continue
            text = source.read_text(encoding="utf-8")
            if package_line.search(text) and declaration.search(text):
                return True
    return False


def check(
    paths: list[Path],
    patched: bool,
    src_roots: list[Path],
    config_dir: Path | None = None,
) -> Report:
    report = Report()
    seen_ids: dict[str, Path] = {}
    for main in paths:
        root = ET.parse(main).getroot()
        if root.tag != "idea-plugin":
            report.error(main, f"root element is <{root.tag}>")
            continue
        id_node = root.find("id")
        plugin_id = (id_node.text or "").strip() if id_node is not None else None
        check_required(root, main, patched, report)
        if plugin_id:
            check_id(plugin_id, main, report)
        check_versions(root, main, report)
        points = declared_points(root, main, plugin_id, report)
        descriptors = [(main, root)]
        for config in optional_configs(root, main, plugin_id, config_dir, report):
            descriptors.append((config, ET.parse(config).getroot()))
        for path, node in descriptors:
            check_extensions(node, path, plugin_id, points, report)
            check_actions(node, path, report, seen_ids)
            if src_roots:
                for fqn in sorted(class_names(node)):
                    if not owned(fqn, src_roots):
                        continue
                    if not resolves(fqn, src_roots):
                        report.error(path, f"class {fqn} has no source file")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check an IntelliJ Platform plugin.xml.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "descriptor", nargs="+", type=Path, help="plugin.xml file(s) to check"
    )
    parser.add_argument(
        "--patched",
        action="store_true",
        help="descriptor was produced by patchPluginXml",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="directory holding optional config files (default: beside it)",
    )
    parser.add_argument(
        "--src-root",
        action="append",
        type=Path,
        default=[],
        help="source root for class resolution (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        report = check(args.descriptor, args.patched, args.src_root, args.config_dir)
    except (ET.ParseError, OSError) as exc:
        print(
            f"ERROR {exc}; expected existing, well-formed plugin.xml files",
            file=sys.stderr,
        )
        return 2
    if args.json:
        document = {
            "findings": report.findings,
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "descriptors": len(args.descriptor),
        }
        print(json.dumps(document, indent=2))
        return 1 if report.errors else 0
    for line in report.errors + report.warnings:
        print(line)
    print(
        f"checked {len(args.descriptor)} descriptor(s): "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
