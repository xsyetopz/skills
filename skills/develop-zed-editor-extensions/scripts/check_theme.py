"""Validate a Zed theme or icon theme JSON file against its published schema.

Stdlib only. Implements the JSON Schema draft-07 keywords that the
published schemas use (type, enum, required, properties,
additionalProperties, items, anyOf, allOf, $ref) and adds the checks that
the schemas cannot express:

- theme: every color parses as #rgb, #rgba, #rrggbb, or #rrggbbaa (the
  formats gpui accepts); style keys absent from the schema are reported,
  because the schema allows unknown keys and Zed drops misspelled ones
  (newer Zed builds also read some keys the v0.2.0 schema lacks); the
  deprecated `scrollbar_thumb.background` key is rejected as the
  `zed-extension` packager rejects it.
- icon theme: every icon path exists under the extension root, and every
  `file_stems`/`file_suffixes` value names a `file_icons` key.

    python3 check_theme.py FILE --schema SCHEMA [--root EXT_DIR] [--json]

Exit status: 0 when no errors, 1 when any error, 2 on bad usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}
Issue = tuple[str, str]
NOT_COLORS = {"background.appearance", "font_style", "font_weight"}


@dataclass
class Finding:
    level: str
    pointer: str
    message: str


def _is_type(value: Any, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


class Validator:
    def __init__(self, schema: dict) -> None:
        self.schema = schema

    def resolve(self, node: dict) -> dict:
        while "$ref" in node:
            ref = node["$ref"]
            if not ref.startswith("#/"):
                raise ValueError(f"unsupported $ref {ref}")
            target: Any = self.schema
            for part in ref[2:].split("/"):
                target = target[part]
            node = target
        return node

    def errors(self, value: Any, node: dict, pointer: str) -> list[Issue]:
        node = self.resolve(node)
        found: list[Issue] = []
        kinds = node.get("type")
        if kinds is not None:
            kinds = [kinds] if isinstance(kinds, str) else kinds
            if not any(_is_type(value, kind) for kind in kinds):
                return [(pointer or "/", f"expected {'|'.join(kinds)}")]
        if "enum" in node and value not in node["enum"]:
            found.append((pointer, f"{value!r} not in {node['enum']}"))
        for sub in node.get("allOf", []):
            found += self.errors(value, sub, pointer)
        if "anyOf" in node:
            options = [self.errors(value, sub, pointer) for sub in node["anyOf"]]
            if all(options):
                found.append((pointer, f"no anyOf branch: {options[0][0][1]}"))
        if isinstance(value, dict):
            found += self._object(value, node, pointer)
        if isinstance(value, list) and "items" in node:
            for index, item in enumerate(value):
                found += self.errors(item, node["items"], f"{pointer}/{index}")
        return found

    def _object(self, value: dict, node: dict, pointer: str) -> list[Issue]:
        found = [
            (pointer or "/", f"missing required `{key}`")
            for key in node.get("required", [])
            if key not in value
        ]
        properties = node.get("properties", {})
        extra = node.get("additionalProperties", True)
        for key, item in value.items():
            child = f"{pointer}/{key}"
            if key in properties:
                found += self.errors(item, properties[key], child)
            elif extra is False:
                found.append((child, "property not allowed"))
            elif isinstance(extra, dict):
                found += self.errors(item, extra, child)
        return found


def check(path: Path, schema: dict, root: Path | None) -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = [
        Finding("ERROR", pointer, message)
        for pointer, message in Validator(schema).errors(data, schema, "")
    ]
    title = schema.get("title", "")
    if title == "ThemeFamilyContent":
        findings += _theme_checks(data, schema)
    elif title == "IconThemeFamilyContent":
        findings += _icon_checks(data, root or path.parent.parent)
    return findings


def _theme_checks(data: dict, schema: dict) -> list[Finding]:
    known = schema["definitions"]["ThemeStyleContent"]["properties"]
    findings = []
    for index, theme in enumerate(data.get("themes", [])):
        style = theme.get("style", {})
        base = f"/themes/{index}/style"
        for key in style:
            if key == "scrollbar_thumb.background":
                findings.append(
                    Finding(
                        "ERROR",
                        f"{base}/{key}",
                        "deprecated; use `scrollbar.thumb.background`",
                    )
                )
            elif key not in known:
                findings.append(
                    Finding(
                        "WARN",
                        f"{base}/{key}",
                        "not in the published "
                        "schema: a typo, or a key newer than the schema",
                    )
                )
        for pointer, color in _colors(style, base):
            if not COLOR_RE.match(color):
                findings.append(Finding("ERROR", pointer, f"bad color {color!r}"))
    return findings


def _colors(value: Any, pointer: str, key: str = ""):
    if isinstance(value, str) and key not in NOT_COLORS:
        yield pointer, value
    elif isinstance(value, dict):
        for child, item in value.items():
            yield from _colors(item, f"{pointer}/{child}", child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _colors(item, f"{pointer}/{index}", key)


def _icon_checks(data: dict, root: Path) -> list[Finding]:
    findings = []
    for index, theme in enumerate(data.get("themes", [])):
        base = f"/themes/{index}"
        icons = theme.get("file_icons", {})
        paths = [
            (f"{base}/file_icons/{name}", entry.get("path"))
            for name, entry in icons.items()
        ]
        for group in ("directory_icons", "chevron_icons"):
            for state, icon in (theme.get(group) or {}).items():
                paths.append((f"{base}/{group}/{state}", icon))
        for name, pair in theme.get("named_directory_icons", {}).items():
            for state, icon in pair.items():
                paths.append((f"{base}/named_directory_icons/{name}/{state}", icon))
        for pointer, icon in paths:
            if icon and not (root / icon).is_file():
                findings.append(Finding("ERROR", pointer, f"missing file {icon}"))
        for group in ("file_stems", "file_suffixes"):
            for key, kind in theme.get(group, {}).items():
                if kind not in icons:
                    findings.append(
                        Finding(
                            "WARN",
                            f"{base}/{group}/{key}",
                            f"{kind!r} is "
                            "not a file_icons key; Zed falls back to its "
                            "default icon theme",
                        )
                    )
    return findings


EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  bad usage: FILE or --schema is missing or is not valid JSON

Output: one "ERROR|WARN POINTER: message" line per finding (a JSON
pointer into FILE), then "N errors, N warnings". --json prints a list of
{level, pointer, message}.

Examples:
  python3 scripts/check_theme.py themes/my-theme.json \\
    --schema schemas/theme-v0.2.0.json
  python3 scripts/check_theme.py icon_themes/icons.json \\
    --schema schemas/icon-theme-v0.2.0.json --root .
  python3 scripts/check_theme.py themes/my-theme.json --schema s.json --json
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", type=Path, help="theme or icon theme JSON file")
    parser.add_argument(
        "--schema", type=Path, required=True, help="the published JSON schema file"
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="extension root that icon paths are relative to (icon themes)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the findings as a JSON list"
    )
    args = parser.parse_args(argv)
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        findings = check(args.file, schema, args.root)
    except (OSError, ValueError) as error:
        print(
            f"{args.file}: {error}; expected FILE and --schema to be readable "
            "JSON files",
            file=sys.stderr,
        )
        return 2
    errors = sum(f.level == "ERROR" for f in findings)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.level} {f.pointer}: {f.message}")
        print(f"{errors} errors, {len(findings) - errors} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
