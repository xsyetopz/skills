"""Check a DuckStation settings.ini against the keys a release wrote.

The bundled key list holds every Section.Key and its default from the
settings.ini that official release v0.1-11826 wrote on a first launch. A key
outside the list is a typo or belongs to another release.

Exit status: 0 when every input passes, 1 when a finding is printed, 2 when an
input file cannot be read (or on a usage error).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KEYS_FILE = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "duckstation-settings-keys-0.1-11826.txt"
)
KEY_VALUE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$")
SECTION = re.compile(r"^\[(.+)\]$")
EPILOG = """\
Exit status:
  0  every file passes ("OK" is printed)
  1  at least one finding
  2  a file (or --keys) cannot be read, or a usage error

Output: one "FILE:LINE: message" line per finding.

Example:
  python3 scripts/check_settings_keys.py ~/.local/share/duckstation/settings.ini
"""


def load_known_keys(path: Path) -> dict[str, str]:
    known: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            name, _, default = line.partition("\t")
            known[name] = default
    return known


def check_settings(path: Path, known: dict[str, str]) -> list[str]:
    findings: list[str] = []
    section = ""
    seen: set[str] = set()
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        where = f"{path}:{number}"
        if not line or line.startswith((";", "#")):
            continue
        header = SECTION.match(line)
        if header:
            section = header.group(1)
            continue
        pair = KEY_VALUE.match(line)
        if pair is None:
            findings.append(f"{where}: not a 'Key = Value' line: {line!r}")
            continue
        if not section:
            findings.append(f"{where}: key before any [Section]")
            continue
        name = f"{section}.{pair.group(1)}"
        if name in seen:
            findings.append(f"{where}: duplicate key {name}")
        seen.add(name)
        if name not in known:
            findings.append(
                f"{where}: {name} is not written by release 0.1-11826; set it"
                " once in the UI and copy the key from settings.ini"
            )
            continue
        value = pair.group(2).strip()
        if known[name] in {"true", "false"} and value not in {"true", "false"}:
            findings.append(f"{where}: {name} expects true or false, got {value!r}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", type=Path, help="settings.ini or game ini")
    parser.add_argument(
        "--keys",
        type=Path,
        default=KEYS_FILE,
        help="known key list (default: the bundled v0.1-11826 list)",
    )
    args = parser.parse_args(argv)

    findings: list[str] = []
    try:
        known = load_known_keys(args.keys)
        for path in args.files:
            findings.extend(check_settings(path, known))
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {getattr(error, 'filename', None) or 'input'}: "
            f"{error}; pass existing UTF-8 files",
            file=sys.stderr,
        )
        return 2
    for finding in findings:
        print(finding)
    if not findings:
        print("OK")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
