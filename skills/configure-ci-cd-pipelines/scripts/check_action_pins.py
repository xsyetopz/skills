#!/usr/bin/env python3
"""Check that GitHub Actions `uses:` references are pinned to commit SHAs.

A tag or branch (`actions/checkout@v7`) can be moved to other code by
whoever controls the action's repository; a full 40-character commit SHA
cannot. Local actions (`./path`) and Docker images pinned by digest
(`docker://image@sha256:...`) are accepted.

With --resolve, each pinned SHA whose line carries a `# vX.Y.Z` comment
is checked through `gh api` to be the commit that tag points to, so the
comment cannot drift from the pin. This needs network access and `gh`.

Usage: check_action_pins.py PATH... [--resolve] [--json]
Exit status: 0 all pinned (and resolved), 1 findings, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

USES = re.compile(
    r"""^\s*(?:-\s*)?uses:\s*['"]?(?P<ref>[^'"\s#]+)['"]?\s*(?:#\s*(?P<comment>\S+))?"""
)
SHA = re.compile(r"^[0-9a-f]{40}$")
FINDING = re.compile(r"^(?P<file>.+?):(?P<line>\d+): (?P<message>.*)$", re.S)
EPILOG = """\
Exit status:
  0  every `uses:` is pinned (and, with --resolve, matches its tag comment)
  1  at least one finding
  2  unreadable input: a PATH does not exist or a file is not UTF-8

Output: one "FILE:LINE: message" line per finding, then "N finding(s)".
--json prints {"findings": [{file, line, message}], "count": N}.

Examples:
  python3 scripts/check_action_pins.py .github/workflows
  python3 scripts/check_action_pins.py .github/workflows --resolve
  python3 scripts/check_action_pins.py .github --json | jq '.findings[].file'
"""


def workflow_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files += sorted(p for p in path.rglob("*") if p.suffix in {".yml", ".yaml"})
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(
                f"{raw} does not exist; pass workflow files or directories"
            )
    return files


def resolve(action: str, tag: str) -> str | None:
    """Return the commit SHA that TAG points to in ACTION's repository."""
    repo = "/".join(action.split("/")[:2])
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{tag}", "--jq", ".sha"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def check_file(path: Path, do_resolve: bool) -> list[str]:
    findings: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = USES.match(line)
        if not match:
            continue
        ref = match.group("ref")
        where = f"{path}:{number}"
        if ref.startswith("./"):
            continue
        if ref.startswith("docker://"):
            if "@sha256:" not in ref:
                findings.append(f"{where}: docker image not pinned by digest: {ref}")
            continue
        action, _, version = ref.partition("@")
        if not SHA.match(version):
            findings.append(
                f"{where}: {action} pinned to {version!r}, not a commit SHA"
            )
            continue
        comment = match.group("comment")
        if do_resolve and comment:
            actual = resolve(action, comment)
            if actual is None:
                findings.append(f"{where}: could not resolve {action}@{comment}")
            elif actual != version:
                findings.append(
                    f"{where}: comment {comment} is {actual[:12]}, pin is {version[:12]}"
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths", nargs="+", help="workflow or action files, or directories"
    )
    parser.add_argument(
        "--resolve",
        action="store_true",
        help="check `# vX.Y.Z` comments against the pinned SHA (needs gh, network)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        findings = [
            f for p in workflow_files(args.paths) for f in check_file(p, args.resolve)
        ]
    except (OSError, UnicodeDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        records = []
        for finding in findings:
            match = FINDING.match(finding)
            assert match, finding  # every finding starts with FILE:LINE
            records.append(
                {
                    "file": match["file"],
                    "line": int(match["line"]),
                    "message": match["message"],
                }
            )
        print(json.dumps({"findings": records, "count": len(records)}, indent=2))
        return 1 if findings else 0
    for finding in findings:
        print(finding)
    print(f"{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
