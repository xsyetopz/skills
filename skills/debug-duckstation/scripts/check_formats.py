"""Check DuckStation settings.ini, .cht cheat/patch, and texture-name syntax.

Rules come from user-facing sources only:
- settings: section/key names and defaults written by the official release
  v0.1-11826 into a fresh portable settings.ini (bundled key list);
- cht: the duckstation/chtdb README "File Format" section;
- texture-name: the DuckStation wiki page "Texture Replacement".

Exit status: 0 when every input passes, 1 when a finding is printed, 2 when
an input file cannot be read (or on a usage error).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

KEYS_FILE = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "examples"
    / "settings"
    / "keys-0.1-11826.txt"
)

FINDING = re.compile(r"^(?P<subject>.+?)(?::(?P<line>\d+))?: (?P<message>.*)$", re.S)
EPILOG = """\
Exit status:
  0  every input passes ("OK" is printed)
  1  at least one finding
  2  an input file (or --keys) cannot be read, or a usage error

Output: one "SUBJECT[:LINE]: message" line per finding, or "OK". Put
--json after the subcommand to print {"findings": [{subject, line,
message}], "count": N}; line is null when a finding has none.

Examples:
  python3 scripts/check_formats.py settings ~/.local/share/duckstation/settings.ini
  python3 scripts/check_formats.py cht cheats/SLUS-00001.cht --json
  python3 scripts/check_formats.py texture-name texupload-0123456789abcdef-...png
"""
CHT_KEYS = frozenset(
    {
        "Type",
        "Activation",
        "Description",
        "Author",
        "Option",
        "OptionRange",
        "OverrideAspectRatio",
        "OverrideCPUOverclock",
        "DisableWidescreenRendering",
        "Enable8MBRAM",
        "DisallowForAchievements",
        "Ignore",
    }
)
CHT_ACTIVATIONS = frozenset({"Manual", "EndFrame"})
CODE_LINE = re.compile(r"^[0-9A-Fa-f?]{8} [0-9A-Fa-f?]{1,8}$")
KEY_VALUE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$")
SECTION = re.compile(r"^\[(.+)\]$")

HASH = r"[0-9A-Fa-f]{16}"
SIZE = r"\d+x\d+"
PALETTED_NAME = re.compile(
    rf"^texupload-P(?P<bits>4|8)-{HASH}-{HASH}-{SIZE}-\d+-\d+-{SIZE}"
    r"-P(?P<first>\d+)-(?P<last>\d+)(?:\.(?:png|jpg|webp))?$"
)
DIRECT_NAME = re.compile(
    rf"^texupload-C16-{HASH}-{SIZE}-\d+-\d+-{SIZE}(?:\.(?:png|jpg|webp))?$"
)


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


def check_cht_metadata(where: str, key: str, value: str) -> list[str]:
    if key not in CHT_KEYS:
        return [f"{where}: unknown metadata key {key!r}"]
    if key == "Type" and value != "Gameshark":
        return [f"{where}: Type must be Gameshark, got {value!r}"]
    if key == "Activation" and value not in CHT_ACTIVATIONS:
        return [f"{where}: Activation must be Manual or EndFrame"]
    if key == "OptionRange":
        low, _, high = value.partition(":")
        try:
            in_order = int(low.strip(), 0) <= int(high.strip(), 0)
        except ValueError:
            in_order = False
        if not in_order:
            return [f"{where}: OptionRange must be min:max with min <= max"]
    return []


@dataclass
class CheatCode:
    lines: int = 0
    has_option: bool = False
    has_wildcard: bool = False


def check_cht(path: Path) -> list[str]:
    findings: list[str] = []
    codes: dict[str, CheatCode] = {}
    current = ""
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        where = f"{path}:{number}"
        if not line or line.startswith((";", "#")):
            continue
        header = SECTION.match(line)
        if header:
            current = header.group(1)
            codes[current] = CheatCode()
            continue
        if not current:
            findings.append(f"{where}: content before the first [Code Name]")
            continue
        state = codes[current]
        pair = KEY_VALUE.match(line)
        if pair is not None:
            findings.extend(check_cht_metadata(where, pair.group(1), pair.group(2)))
            if pair.group(1) in {"Option", "OptionRange"}:
                state.has_option = True
            continue
        if CODE_LINE.match(line) is None:
            findings.append(f"{where}: not a code line 'XXXXXXXX Y[...Y]'")
            continue
        state.lines += 1
        state.has_wildcard = state.has_wildcard or "?" in line
    for name, state in codes.items():
        if not state.lines:
            findings.append(f"{path}: [{name}] has no code body")
        if state.has_wildcard and not state.has_option:
            findings.append(f"{path}: [{name}] uses '?' without Option(Range)")
    return findings


def check_texture_name(name: str) -> list[str]:
    paletted = PALETTED_NAME.match(name)
    if paletted:
        if int(paletted.group("first")) > int(paletted.group("last")):
            return [f"{name}: palette range start is after its end"]
        return []
    if DIRECT_NAME.match(name):
        return []
    return [f"{name}: does not match the wiki texupload-... format"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print a JSON report")
    sub = parser.add_subparsers(dest="kind", required=True)
    settings = sub.add_parser(
        "settings", parents=[common], help="settings.ini or game ini"
    )
    settings.add_argument("files", nargs="+", type=Path)
    settings.add_argument(
        "--keys",
        type=Path,
        default=KEYS_FILE,
        help="known key list (default: the bundled v0.1-11826 list)",
    )
    cht = sub.add_parser("cht", parents=[common], help="cheat or patch .cht file")
    cht.add_argument("files", nargs="+", type=Path)
    texture = sub.add_parser(
        "texture-name", parents=[common], help="dump/replacement file name"
    )
    texture.add_argument("names", nargs="+")
    args = parser.parse_args(argv)

    findings: list[str] = []
    try:
        if args.kind == "settings":
            known = load_known_keys(args.keys)
            for path in args.files:
                findings.extend(check_settings(path, known))
        elif args.kind == "cht":
            for path in args.files:
                findings.extend(check_cht(path))
        else:
            for name in args.names:
                findings.extend(check_texture_name(name))
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {getattr(error, 'filename', None) or 'input'}: "
            f"{error}; pass existing UTF-8 files",
            file=sys.stderr,
        )
        return 2
    if args.json:
        records = []
        for finding in findings:
            match = FINDING.match(finding)
            subject, line, message = (
                (match["subject"], match["line"], match["message"])
                if match
                else (None, None, finding)
            )
            records.append(
                {
                    "subject": subject,
                    "line": int(line) if line else None,
                    "message": message,
                }
            )
        print(json.dumps({"findings": records, "count": len(records)}, indent=2))
        return 1 if findings else 0
    for finding in findings:
        print(finding)
    if not findings:
        print("OK")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
