#!/usr/bin/env python3
"""Validate a JSON document against a JSON Schema (draft-07 subset).

Supports exactly the keywords used by the Codex hook schemas:
type (string or list), properties, required, additionalProperties
(boolean), enum, const, allOf, $ref to #/definitions/..., and boolean
schemas. Any other validation keyword stops with exit 2, so an
unsupported schema is never reported as valid.

Usage: validate_schema.py SCHEMA DOCUMENT   (DOCUMENT "-" reads stdin)
Exit status: 0 valid, 1 invalid (errors printed), 2 unsupported or bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ANNOTATIONS = {"$schema", "title", "description", "default", "definitions"}
SUPPORTED = ANNOTATIONS | {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "enum",
    "const",
    "allOf",
    "$ref",
}
TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}
EPILOG = """\
Exit status:
  0  valid
  1  invalid; one "PATH: message" line per error, then "N error(s)"
  2  usage error, unreadable or non-JSON input, or a schema this subset
     cannot evaluate (unsupported keyword, unresolved $ref, $ref cycle)

Output: error lines then "valid" or "N error(s)". --json prints
{"valid": BOOL, "errors": [MESSAGE, ...]} instead; nothing is printed on
stdout for exit 2 (the reason goes to stderr).

Examples:
  python3 scripts/validate_schema.py \\
      assets/schemas/codex-0.157.0/stop.command.input.schema.json payload.json
  python3 handler.py <payload.json | python3 scripts/validate_schema.py \\
      assets/schemas/codex-0.157.0/stop.command.output.schema.json - --json
"""


class Unsupported(Exception):
    pass


def type_matches(value: Any, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name not in TYPES:
        raise Unsupported(f"type {name!r}")
    expected = TYPES[name]
    if expected is str and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def resolve(root: dict, ref: str) -> Any:
    prefix = "#/definitions/"
    if not ref.startswith(prefix):
        raise Unsupported(f"$ref {ref!r}")
    definitions = root.get("definitions")
    name = ref[len(prefix) :]
    if not isinstance(definitions, dict) or name not in definitions:
        raise Unsupported(f"$ref {ref!r} has no matching definition")
    return definitions[name]


def validate(root: dict, schema: Any, value: Any, path: str = "$") -> list[str]:
    if schema is True:
        return []
    if schema is False:
        return [f"{path}: no value is allowed here"]
    if not isinstance(schema, dict):
        raise Unsupported(f"schema at {path} is {type(schema).__name__}, not an object")
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise Unsupported(f"keywords {sorted(unknown)} at {path}")
    errors: list[str] = []
    if "$ref" in schema:
        errors += validate(root, resolve(root, schema["$ref"]), value, path)
    for part in schema.get("allOf", []):
        errors += validate(root, part, value, path)
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type_matches(value, n) for n in names):
            return [*errors, f"{path}: expected {'/'.join(names)}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}: missing required {name!r}")
        for name, item in value.items():
            if name in properties:
                errors += validate(root, properties[name], item, f"{path}.{name}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property {name!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("schema", type=Path, help="JSON Schema file")
    parser.add_argument("document", help='JSON document file, or "-" for stdin')
    parser.add_argument(
        "--json", action="store_true", help="print one JSON result on stdout"
    )
    args = parser.parse_args(argv)
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        text = (
            sys.stdin.read()
            if args.document == "-"
            else Path(args.document).read_text(encoding="utf-8")
        )
        document = json.loads(text)
        errors = validate(schema, schema, document)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except Unsupported as error:
        print(f"unsupported schema: {error}", file=sys.stderr)
        return 2
    except RecursionError:
        print("unsupported schema: nesting too deep (a $ref cycle?)", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 1 if errors else 0
    for message in errors:
        print(message)
    print("valid" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
