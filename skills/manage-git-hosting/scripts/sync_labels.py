#!/usr/bin/env python3
"""Plan (and optionally apply) GitHub label changes to match a JSON file.

Reads the repository's labels with `gh label list`, compares them with
the desired set, and prints one line per change. Nothing is written
unless --apply is given; with --apply each change runs as one `gh label`
command, so a rerun after a partial failure only repeats what is still
missing. Labels not in the file are left alone unless --prune is given.

Desired file: [{"name": "bug", "color": "d73a4a", "description": "..."}]

Usage: sync_labels.py REPO DESIRED.json [--apply] [--prune] [--json]
Exit status: 0 success (plan printed or applied), 1 a gh command failed,
2 bad input.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

EPILOG = """\
Exit status:
  0  success: the plan was printed, or every change was applied
  1  a `gh label` write failed (earlier changes stay applied; rerun)
  2  bad input: unreadable DESIRED file, `gh` missing, or `gh label list`
     failed (not authenticated, unknown REPO)

Output: "plan gh label ..." per change (or "run  gh label ..." with
--apply), or "labels already match; nothing to do". --json prints
{"repo", "applied", "changes": [{action, label, command, status}]},
where status is "planned", "applied", or "failed".

Examples:
  python3 scripts/sync_labels.py acme/app labels.json
  python3 scripts/sync_labels.py acme/app labels.json --prune
  python3 scripts/sync_labels.py acme/app labels.json --apply
"""


def gh(*args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        raise RuntimeError(
            "gh not found on PATH; install GitHub CLI and run `gh auth login`"
        ) from None


def current_labels(repo: str) -> dict[str, dict]:
    result = gh(
        "label",
        "list",
        "-R",
        repo,
        "--limit",
        "1000",
        "--json",
        "name,color,description",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gh label list failed")
    return {label["name"].lower(): label for label in json.loads(result.stdout)}


def plan(current: dict[str, dict], desired: list[dict], prune: bool) -> list[list[str]]:
    commands: list[list[str]] = []
    wanted = {d["name"].lower() for d in desired}
    for label in desired:
        color = label.get("color", "ededed").lower().lstrip("#")
        description = label.get("description", "")
        have = current.get(label["name"].lower())
        if have is None:
            commands.append(
                [
                    "create",
                    label["name"],
                    "--color",
                    color,
                    "--description",
                    description,
                ]
            )
        elif (have["color"].lower(), have.get("description", "")) != (
            color,
            description,
        ):
            commands.append(
                ["edit", have["name"], "--color", color, "--description", description]
            )
    if prune:
        for key, have in sorted(current.items()):
            if key not in wanted:
                commands.append(["delete", have["name"], "--yes"])
    return commands


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo", help="OWNER/REPO")
    parser.add_argument("desired", type=Path, help="desired labels JSON file")
    parser.add_argument(
        "--apply", action="store_true", help="run the changes (default: plan only)"
    )
    parser.add_argument(
        "--prune", action="store_true", help="also delete labels not in DESIRED"
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        desired = json.loads(args.desired.read_text(encoding="utf-8"))
        if not isinstance(desired, list) or not all("name" in d for d in desired):
            raise ValueError("desired file must be a list of objects with name")
        commands = plan(current_labels(args.repo), desired, args.prune)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        return report_json(args.repo, commands, args.apply)
    if not commands:
        print("labels already match; nothing to do")
        return 0
    for command in commands:
        print(("run  " if args.apply else "plan ") + "gh label " + " ".join(command))
        if args.apply:
            result = gh("label", *command, "-R", args.repo)
            if result.returncode != 0:
                print(f"error: {result.stderr.strip()}", file=sys.stderr)
                return 1
    return 0


def report_json(repo: str, commands: list[list[str]], apply: bool) -> int:
    changes = [
        {
            "action": command[0],
            "label": command[1],
            "command": ["gh", "label", *command, "-R", repo],
            "status": "planned",
        }
        for command in commands
    ]
    status = 0
    for change, command in zip(changes, commands, strict=True):
        if not apply:
            break
        result = gh("label", *command, "-R", repo)
        if result.returncode != 0:
            print(f"error: {result.stderr.strip()}", file=sys.stderr)
            change["status"], status = "failed", 1
            break
        change["status"] = "applied"
    print(json.dumps({"repo": repo, "applied": apply, "changes": changes}, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
