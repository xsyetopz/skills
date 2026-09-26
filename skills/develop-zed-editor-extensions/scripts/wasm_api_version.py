"""Print the `zed:api-version` a compiled Zed extension declares.

Stdlib only. `zed_extension_api` embeds its own version as a 6-byte
custom section named `zed:api-version` (three big-endian u16 values).
Zed reads that section to pick the host interface and refuses versions
outside its supported range. A wasm32-wasip2 build is a component, so
the section sits inside a nested core module; this walks both layers.

    python3 wasm_api_version.py FILE.wasm [--max MAJOR.MINOR.PATCH] [--json]

Exit status: 0 on success, 1 when the version exceeds --max, 2 when the
file is not wasm or has no valid section.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAGIC = b"\0asm"
SECTION = "zed:api-version"
COMPONENT_LAYER = b"\x0d\x00\x01\x00"
CORE_MODULE_SECTION = 1
EPILOG = """\
Exit status:
  0  the version was read (and is not newer than --max)
  1  the version is newer than --max
  2  FILE is unreadable, not WebAssembly, or has no valid zed:api-version

Output: "zed:api-version MAJOR.MINOR.PATCH" on stdout. --json prints
{"file", "api_version", "max", "within_max"}; within_max is null without
--max.

Examples:
  python3 scripts/wasm_api_version.py extension.wasm
  python3 scripts/wasm_api_version.py extension.wasm --max 0.7.0
  python3 scripts/wasm_api_version.py extension.wasm --json
"""


def version_limit(text: str) -> tuple[int, int, int]:
    """Parse --max; missing parts are 0, so 0.7 means 0.7.0."""
    if not re.fullmatch(r"\d+(\.\d+){0,2}", text):
        raise argparse.ArgumentTypeError(
            f"expected MAJOR.MINOR.PATCH such as 0.7.0, got {text!r}"
        )
    major, minor, patch = (*map(int, text.split(".")), 0, 0)[:3]
    return major, minor, patch


def _leb128(data: bytes, offset: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, offset


def find_versions(data: bytes) -> list[tuple[int, int, int]]:
    """Return every zed:api-version value in a module or component."""
    if data[:4] != MAGIC:
        raise ValueError("not a WebAssembly binary")
    is_component = data[4:8] == COMPONENT_LAYER
    versions = []
    offset = 8
    while offset < len(data):
        section_id = data[offset]
        size, offset = _leb128(data, offset + 1)
        body = data[offset : offset + size]
        if section_id == 0:
            name_len, start = _leb128(body, 0)
            name = body[start : start + name_len].decode("utf-8", "replace")
            payload = body[start + name_len :]
            if name == SECTION:
                if len(payload) != 6:
                    raise ValueError(f"{SECTION} has {len(payload)} bytes, not 6")
                major, minor, patch = (
                    int.from_bytes(payload[i : i + 2], "big") for i in (0, 2, 4)
                )
                versions.append((major, minor, patch))
        elif is_component and section_id == CORE_MODULE_SECTION:
            versions += find_versions(body)
        offset += size
    return versions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("wasm", type=Path, help="compiled extension (.wasm)")
    parser.add_argument(
        "--max",
        type=version_limit,
        metavar="MAJOR.MINOR.PATCH",
        help="highest version the target Zed accepts",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        versions = find_versions(args.wasm.read_bytes())
    except (OSError, ValueError, IndexError) as error:
        print(
            f"{args.wasm}: {error}; expected a wasm32-wasip2 build of a Zed extension",
            file=sys.stderr,
        )
        return 2
    if not versions:
        print(
            f"{args.wasm}: no {SECTION} section; the module was not built with "
            "zed_extension_api",
            file=sys.stderr,
        )
        return 2
    version = versions[0]
    text = ".".join(map(str, version))
    limit_text = ".".join(map(str, args.max)) if args.max else None
    too_new = args.max is not None and version > args.max
    if args.json:
        report = {
            "file": str(args.wasm),
            "api_version": text,
            "max": limit_text,
            "within_max": None if args.max is None else not too_new,
        }
        print(json.dumps(report, indent=2))
    else:
        print(f"{SECTION} {text}")
    if too_new:
        print(f"{text} is newer than {limit_text}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
