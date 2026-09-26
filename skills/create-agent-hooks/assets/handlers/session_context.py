#!/usr/bin/env python3
"""SessionStart hook: give the agent the branch and changed files.

For Claude Code and Codex, which both accept
{"hookSpecificOutput": {"hookEventName": "SessionStart",
"additionalContext": ...}}. Runs `git` in the event's cwd with a short
timeout; outside a repository it adds nothing.

Usage: session_context.py [--max-files 20]
Exit status: 0 for any valid event; 2 for an invalid event.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

LIMIT = 1024 * 1024


def git(cwd: str, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--max-files", type=int, default=20)
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(LIMIT + 1)
    try:
        event = json.loads(raw.decode("utf-8")) if len(raw) <= LIMIT else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        event = None
    if not isinstance(event, dict) or not isinstance(event.get("cwd"), str):
        print("session_context: expected an event object with cwd", file=sys.stderr)
        return 2
    # --show-current also works before the first commit (unborn branch),
    # where `rev-parse --abbrev-ref HEAD` fails; it prints "" when detached.
    branch = git(event["cwd"], "branch", "--show-current")
    status = git(event["cwd"], "status", "--porcelain")
    if branch is None or status is None:
        return 0  # not a repository: no context, no error
    changed = [line[3:] for line in status.splitlines() if line.strip()]
    shown = changed[: args.max_files]
    name = branch.strip() or "(detached HEAD)"
    lines = [f"Branch: {name}", f"Changed files: {len(changed)}"]
    lines += [f"- {path}" for path in shown]
    if len(changed) > len(shown):
        lines.append(f"- ... {len(changed) - len(shown)} more")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
