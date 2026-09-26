"""Stdlib fallback secret scanner for when gitleaks is not installed.

Usage: python3 scan_secrets.py PATH... [--json] [--limit N]

Prints one redacted line per match (rule, path:line, first four characters)
and exits 1 if anything matched, 0 otherwise. The rules are deliberately few
and high-signal; gitleaks ships far more. Matches are leads: confirm each by
reading the line and asking the owner, never by trying the credential.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DESCRIPTION = "Stdlib fallback secret scanner for when gitleaks is not installed."

RULES: dict[str, re.Pattern[str]] = {
    # AWS IAM unique-ID prefixes: AKIA access key, ASIA temporary key.
    "aws-access-key-id": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    # GitHub documents these token prefixes.
    "github-token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
    ),
    # RFC 7468 private-key labels plus legacy "RSA/EC/OPENSSH" forms.
    "private-key": re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
    "assigned-secret": re.compile(
        r"(?i)\b\w*(?:password|passwd|secret|api[_-]?key|token)\w*\s*[:=]\s*"
        r"['\"]([^'\"\s]{8,})['\"]"
    ),
}
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "target"}
MAX_BYTES = 2_000_000
EPILOG = """\
Exit status:
  0  no matches
  1  at least one match
  2  bad usage: a PATH does not exist

Output: one "RULE<TAB>PATH:LINE<TAB>PREVIEW" line per match (the preview
keeps only the first four characters), then "N match(es)" counting every
match. --json prints a list of {rule, path, line, preview}. --limit N
prints at most N matches (the count and exit status still cover all) and
notes the omission on stderr. Files over 2 MB and binary files are skipped.

Examples:
  python3 scripts/scan_secrets.py .
  python3 scripts/scan_secrets.py src config --limit 50
  python3 scripts/scan_secrets.py . --json | jq 'group_by(.rule) | map(length)'
"""


@dataclass(frozen=True)
class Match:
    rule: str
    path: str
    line: int
    preview: str


def redact(value: str) -> str:
    return value[:4] + "..." if len(value) > 4 else "..."


def scan_text(path: str, text: str) -> list[Match]:
    found: list[Match] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in RULES.items():
            for hit in pattern.finditer(line):
                value = hit.group(hit.lastindex or 0)
                found.append(Match(rule, path, number, redact(value)))
    return found


def iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )


def scan_paths(paths: list[Path]) -> list[Match]:
    found: list[Match] = []
    for root in paths:
        for path in iter_files(root):
            try:
                if path.stat().st_size > MAX_BYTES:
                    continue
                data = path.read_bytes()
            except OSError as error:
                print(f"SKIP {path}: {error}", file=sys.stderr)
                continue
            if b"\0" in data:
                continue  # binary
            found.extend(scan_text(str(path), data.decode("utf-8", "replace")))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", type=Path, help="files or directories")
    parser.add_argument("--json", action="store_true", help="print a JSON list")
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="print at most N matches (default: all)",
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be 0 or more")
    missing = [str(path) for path in args.paths if not path.exists()]
    if missing:
        print(
            f"error: no such file or directory: {', '.join(missing)}; "
            "pass existing files or directories to scan",
            file=sys.stderr,
        )
        return 2
    found = scan_paths(args.paths)
    shown = found if args.limit is None else found[: args.limit]
    if len(shown) < len(found):
        print(
            f"showing {len(shown)} of {len(found)} matches; raise --limit for more",
            file=sys.stderr,
        )
    if args.json:
        print(json.dumps([asdict(m) for m in shown], indent=2))
    else:
        for m in shown:
            print(f"{m.rule}\t{m.path}:{m.line}\t{m.preview}")
        print(f"{len(found)} match(es)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
