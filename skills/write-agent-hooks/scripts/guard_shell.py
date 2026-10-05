#!/usr/bin/env python3
"""Pre-tool-use guard: deny shell commands that match a deny pattern.

Claude Code and Codex send the same PreToolUse payload and accept the
same deny shape. Allowed commands produce no decision, so the host's
normal permission flow still applies.

Usage: guard_shell.py [--deny REGEX ...]
  Default deny patterns: `git push --force`, `-f` (also combined, as in
  `-fu`), a `+refspec`, a lease without an expected SHA
  (`--force-with-lease` or `--force-with-lease=REF`), `rm -rf /`, and
  `rm -rf ~`. `--force-with-lease=REF:SHA` is allowed. Each --deny adds a
  pattern.

Exit status: 0 with the host's JSON decision (or no output to allow);
2 with a reason on stderr when stdin is not a valid event or a --deny
pattern is not a valid regex (fail closed).
"""

from __future__ import annotations

import argparse
import json
import re
import sys

LIMIT = 1024 * 1024
DEFAULT_DENY = {
    # Global options such as `-C DIR` may precede `push`; the flag search
    # stops at `;`, `&`, `|`, or a newline so a later command is not read.
    # A lease without `:SHA` compares against the remote-tracking ref, which
    # a background fetch refreshes, so it is treated as a plain force push.
    "force push": (
        r"\bgit(\s+-\S+(\s+[^-\s]\S*)?)*\s+push\b[^;&|\n]*"
        r"\s(--force|--force-with-lease(=[^\s:]*)?|-[a-zA-Z]*f[a-zA-Z]*|\+\S+)"
        r"(\s|$)"
    ),
    "recursive delete of / or ~": (
        r"\brm\s+-[a-zA-Z]*([rR][a-zA-Z]*f|f[a-zA-Z]*[rR])[a-zA-Z]*\s+(/|~)(\s|$)"
    ),
}

SHELL_TOOL = "Bash"  # both hosts name their shell tool Bash


EPILOG = """\
Exit status:
  0  allow (no output) or deny (the JSON deny decision printed)
  2  stdin is not a valid event, or a --deny regex is invalid (reason on
     stderr; fails closed)

Examples:
  python3 guard_shell.py < pretooluse-event.json
  python3 guard_shell.py --deny 'curl .* \\| sh' < event.json
"""


class BadEvent(ValueError):
    pass


def read_event() -> dict:
    raw = sys.stdin.buffer.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise BadEvent("input exceeds 1 MiB")
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BadEvent(f"input is not JSON: {error}") from None
    if not isinstance(event, dict):
        raise BadEvent("input is not a JSON object")
    return event


def shell_command(event: dict) -> str | None:
    """Return the shell command, or None when the tool is not a shell."""
    tool, args = event.get("tool_name"), event.get("tool_input")
    if not isinstance(tool, str):
        raise BadEvent("missing tool name")
    if tool != SHELL_TOOL or not isinstance(args, dict):
        return None
    command = args.get("command")
    return command if isinstance(command, str) else None


def deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--deny", action="append", default=[])
    args = parser.parse_args(argv)
    rules = {**DEFAULT_DENY, **{p: p for p in args.deny}}
    try:
        patterns = {label: re.compile(regex) for label, regex in rules.items()}
    except re.error as error:
        print(
            f"guard_shell: invalid --deny pattern: {error}; blocking", file=sys.stderr
        )
        return 2
    try:
        command = shell_command(read_event())
    except BadEvent as error:
        print(f"guard_shell: {error}; blocking", file=sys.stderr)
        return 2
    if command is None:
        return 0
    for label, pattern in patterns.items():
        if pattern.search(command):
            reason = f"Blocked by guard_shell ({label}): {command[:200]}"
            print(json.dumps(deny(reason)))
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
