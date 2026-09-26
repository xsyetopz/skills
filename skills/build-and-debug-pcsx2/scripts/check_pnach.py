"""Check PCSX2 .pnach files against the rules of PCSX2's own patch loader.

The rules mirror pcsx2/Patch.cpp at commit 2c804670 (v2.9.84). The loader
logs a console error and drops a malformed line; it never stops the game.
This checker reports the same lines before boot:

- error: the loader rejects the line (the patch silently does nothing).
- warning: the loader accepts the line but behaves in a way that is easy to
  miss (ignored key, truncated text, dropped nibble, skipped group).

Exit status: 0 when no errors, 1 when any error, 2 for usage problems.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PLACES = ("0", "1", "2", "3")
CPUS = ("EE", "IOP")
TYPES = (
    "byte",
    "short",
    "word",
    "double",
    "extended",
    "beshort",
    "beword",
    "bedouble",
    "bytes",
)
TYPE_BYTES = {
    "byte": 1,
    "short": 2,
    "word": 4,
    "double": 8,
    "beshort": 2,
    "beword": 4,
    "bedouble": 8,
}
# Keys the loader executes or shows in the UI; "gametitle" is documented in
# the upstream example file and ignored by the loader.
KNOWN_KEYS = {
    "patch",
    "dpatch",
    "gsaspectratio",
    "gsinterlacemode",
    "author",
    "description",
    "comment",
    "gametitle",
}
TEXT_KEYS = {"author", "description", "comment", "gametitle"}
INTERLACE_MODES = range(10)  # GSInterlaceMode::Automatic .. AdaptiveBFF
# FindPatchFilesOnDisk globs SERIAL_CRC*.pnach and CRC*.pnach through
# StringUtil::WildcardMatch, which compares characters with tolower().
FILENAME_RE = re.compile(r"^(?:[^_]+_)?[0-9A-F]{8}.*\.pnach$", re.IGNORECASE)
HEX_RE = re.compile(r"^[0-9A-Fa-f]+$")
# The loader parses decimals with std::from_chars, which accepts ASCII only.
DECIMAL_RE = re.compile(r"[0-9]+")
EPILOG = """\
Exit status:
  0  no errors (warnings allowed)
  1  at least one error: the loader would drop that line
  2  usage error, or an input is not a readable file

Output: one "FILE:LINE: LEVEL: message" line per finding (LINE 0 is the
file name itself), then "N errors, M warnings". --limit N prints only the
first N findings (the summary still counts all; a note goes to stderr).
--json prints {"findings": [{file, line, level, message}], "errors": N,
"warnings": M} instead; --limit caps the list there too.

Examples:
  python3 scripts/check_pnach.py patches/SLUS-20062_ABCDEF01.pnach
  python3 scripts/check_pnach.py cheats/*.pnach --limit 50
  python3 scripts/check_pnach.py cheats/SLUS-20062_ABCDEF01.pnach --json
"""


@dataclass(frozen=True)
class Finding:
    line: int
    level: str
    message: str


def parse_hex(text: str, max_bits: int) -> int | None:
    """Parse like std::from_chars(base 16) with a full-consumption check."""
    if not HEX_RE.match(text):
        return None
    value = int(text, 16)
    if value >= 1 << max_bits:
        return None
    return value


def trim_line(raw: str) -> str:
    """Patch::TrimPatchLine: strip, then cut everything from the first //."""
    line = raw.strip()
    pos = line.find("//")
    if pos != -1:
        line = line[:pos]
    return line.strip()


def check_patch(value: str, lineno: int) -> list[Finding]:
    out: list[Finding] = []
    pieces = [p.strip() for p in value.split(",")]
    if len(pieces) != 5:
        return [
            Finding(
                lineno,
                "error",
                f"Expected 5 data parameters; only found {len(pieces)}",
            )
        ]
    place, cpu, addr_text, type_name, data_text = pieces
    if place not in PLACES:
        out.append(Finding(lineno, "error", f"Invalid 'place' value '{place}'"))
    addr = parse_hex(addr_text, 32)
    if addr is None:
        out.append(
            Finding(
                lineno,
                "error",
                f"Malformed address '{addr_text}', a hex number without "
                "prefix (e.g. 0123ABCD) is expected",
            )
        )
    if cpu not in CPUS:
        out.append(Finding(lineno, "error", f"Unrecognized CPU Target: '{cpu}'"))
    if type_name not in TYPES:
        out.append(
            Finding(lineno, "error", f"Unrecognized Operand Size: '{type_name}'")
        )
        return out
    if type_name == "bytes":
        if not data_text or not HEX_RE.match(data_text):
            out.append(
                Finding(
                    lineno,
                    "error",
                    f"Malformed data '{data_text}', a hex string without "
                    "prefix (e.g. 0123ABCD) is expected",
                )
            )
        elif len(data_text) % 2:
            out.append(
                Finding(
                    lineno,
                    "warning",
                    "odd-length 'bytes' data: the loader drops the last nibble",
                )
            )
        return out
    data = parse_hex(data_text, 64)
    if data is None:
        out.append(
            Finding(
                lineno,
                "error",
                f"Malformed data '{data_text}', a hex number without prefix "
                "(e.g. 0123ABCD) is expected",
            )
        )
    elif type_name in TYPE_BYTES and data >= 1 << (8 * TYPE_BYTES[type_name]):
        out.append(
            Finding(
                lineno,
                "warning",
                f"data {data_text} is wider than {type_name}; "
                "only the low-order bytes are written",
            )
        )
    return out


def check_dpatch(value: str, lineno: int) -> list[Finding]:
    pieces = [p.strip() for p in value.split(",")]
    if len(pieces) < 3:
        return [
            Finding(
                lineno,
                "error",
                f"Expected at least 3 data parameters; only found {len(pieces)}",
            )
        ]
    if not DECIMAL_RE.fullmatch(pieces[0]):
        return [Finding(lineno, "error", f"Malformed version/type '{pieces[0]}'")]
    if int(pieces[0]) != 0:
        return [
            Finding(
                lineno,
                "error",
                f"Unsupported version/type '{pieces[0]}', only 0 is supported",
            )
        ]
    patterns = parse_hex(pieces[1], 32)
    replacements = parse_hex(pieces[2], 32)
    if patterns is None:
        return [Finding(lineno, "error", "Malformed number of patterns")]
    if replacements is None:
        return [Finding(lineno, "error", "Malformed number of replacements")]
    expected = 3 + 2 * (patterns + replacements)
    if len(pieces) != expected:
        return [
            Finding(
                lineno,
                "error",
                f"Expected 2 fields for each {patterns} patterns and "
                f"{replacements} replacements; found {len(pieces) - 3}",
            )
        ]
    out: list[Finding] = []
    for index in range(3, len(pieces), 2):
        offset = parse_hex(pieces[index], 32)
        word = parse_hex(pieces[index + 1], 32)
        if offset is None:
            out.append(Finding(lineno, "error", f"Malformed offset '{pieces[index]}'"))
        elif offset % 4:
            out.append(
                Finding(
                    lineno,
                    "warning",
                    f"offset {pieces[index]} is not a multiple of 4",
                )
            )
        if word is None:
            out.append(
                Finding(lineno, "error", f"Malformed value '{pieces[index + 1]}'")
            )
    return out


def check_aspect(value: str, lineno: int) -> list[Finding]:
    match = re.fullmatch(r"\s*(\d+)\s*:\s*(\d+)\s*", value)
    if match and int(match[2]) != 0 and int(match[1]) > 0:
        return []
    return [
        Finding(
            lineno,
            "error",
            f"{value} is an unknown aspect ratio (the loader parses N:M only)",
        )
    ]


def check_interlace(value: str, lineno: int) -> list[Finding]:
    if DECIMAL_RE.fullmatch(value) and int(value) in INTERLACE_MODES:
        return []
    return [Finding(lineno, "error", f"{value} is an unknown interlace mode")]


def check_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    groups: set[str] = set()
    current: str | None = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = trim_line(raw)
        if not line:
            continue
        if line.startswith("["):
            if len(line) < 2 or not line.endswith("]"):
                findings.append(
                    Finding(lineno, "error", f"Malformed patch line: {line}")
                )
                continue
            current = line[1:-1]
            if not current:
                findings.append(
                    Finding(lineno, "error", f"Malformed patch name: {line}")
                )
            elif current in groups:
                findings.append(
                    Finding(
                        lineno,
                        "warning",
                        f"duplicate group [{current}] is skipped by the loader",
                    )
                )
            groups.add(current)
            continue
        if "=" not in line:
            findings.append(
                Finding(lineno, "warning", "line has no '=' and is ignored")
            )
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key in TEXT_KEYS and "://" in raw:
            findings.append(
                Finding(lineno, "warning", f"{key} is cut at '//' (URL truncated)")
            )
        if key not in KNOWN_KEYS:
            findings.append(
                Finding(lineno, "warning", f"unknown key '{key}' is ignored")
            )
            continue
        if key in ("patch", "dpatch") and current is None:
            findings.append(
                Finding(
                    lineno,
                    "warning",
                    f"{key} before the first [group] is always on (legacy)",
                )
            )
        if key == "patch" and current is None:
            findings.append(
                Finding(
                    lineno,
                    "warning",
                    "an unlabelled patch in patches/ disables patches.zip "
                    "for this game",
                )
            )
        if key == "patch":
            findings.extend(check_patch(value, lineno))
        elif key == "dpatch":
            findings.extend(check_dpatch(value, lineno))
        elif key == "gsaspectratio":
            findings.extend(check_aspect(value, lineno))
        elif key == "gsinterlacemode":
            findings.extend(check_interlace(value, lineno))
    return findings


def check_file(path: Path) -> list[Finding]:
    findings = check_text(path.read_text(encoding="utf-8", errors="replace"))
    if not FILENAME_RE.match(path.name):
        findings.insert(
            0,
            Finding(
                0,
                "warning",
                "file name does not match SERIAL_CRC*.pnach or CRC*.pnach "
                "(CRC = 8 hex digits); the loader will not find it",
            ),
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    summary = __doc__.split("\n", 1)[0] if __doc__ is not None else None
    parser = argparse.ArgumentParser(
        description=summary,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", type=Path, help=".pnach files")
    parser.add_argument(
        "--json", action="store_true", help="print one JSON report on stdout"
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="print at most N findings (default: all)",
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be 0 or more")
    errors = warnings = shown = 0
    records: list[dict[str, object]] = []
    for path in args.files:
        if not path.is_file():
            print(f"{path}: not a file", file=sys.stderr)
            return 2
        try:
            findings = check_file(path)
        except OSError as error:
            print(
                f"{path}: cannot read: {error.strerror or error}; "
                "pass readable .pnach files",
                file=sys.stderr,
            )
            return 2
        for finding in findings:
            if finding.level == "error":
                errors += 1
            else:
                warnings += 1
            if args.limit is not None and shown >= args.limit:
                continue
            shown += 1
            if args.json:
                records.append(
                    {
                        "file": str(path),
                        "line": finding.line,
                        "level": finding.level,
                        "message": finding.message,
                    }
                )
            else:
                print(f"{path}:{finding.line}: {finding.level}: {finding.message}")
    if shown < errors + warnings:
        print(
            f"showing {shown} of {errors + warnings} findings; raise --limit for more",
            file=sys.stderr,
        )
    if args.json:
        report = {"findings": records, "errors": errors, "warnings": warnings}
        print(json.dumps(report, indent=2))
    else:
        print(f"{errors} errors, {warnings} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
