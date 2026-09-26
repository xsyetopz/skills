#!/usr/bin/env python3
"""Pre-tool-use guard: deny shell commands that match a deny pattern.

One script, one policy, one adapter per host. The adapter reads the
host's documented input shape and writes the host's documented deny
shape. Allowed commands produce no decision, so the host's normal
permission flow still applies.

Usage: guard_shell.py --host HOST [--deny REGEX ...]
  HOST: claude | codex | gemini | cursor | copilot | copilot-pascal | vscode
  Default deny patterns: `git push --force`/`-f`, `rm -rf /`, `rm -rf ~`.

Exit status: 0 with the host's JSON decision (or no output to allow);
2 with a reason on stderr when stdin is not a valid event (fail closed).
"""

from __future__ import annotations

import argparse
import json
import re
import sys

LIMIT = 1024 * 1024
DEFAULT_DENY = {
    "force push": r"\bgit\s+push\b.*\s(--force|-f)(\s|$)",
    "recursive delete of / or ~": r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+(/|~)(\s|$)",
}

# Tool names each host uses for its shell tool (from the hosts' docs).
SHELL_TOOLS = {
    "claude": {"Bash"},
    "codex": {"Bash"},
    "gemini": {"run_shell_command"},
    "cursor": {"Shell"},
    "copilot": {"bash"},
    "copilot-pascal": {"Bash"},
    "vscode": None,  # Local harness tool names: read them from debug logs
}


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


def shell_command(host: str, event: dict) -> str | None:
    """Return the shell command, or None when the tool is not a shell."""
    if host == "copilot" and "toolName" in event:
        tool, args = event.get("toolName"), event.get("toolArgs")
        if isinstance(args, str):  # toolArgs may arrive as a JSON string
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                raise BadEvent("toolArgs is not JSON") from None
    else:
        tool, args = event.get("tool_name"), event.get("tool_input")
    names = SHELL_TOOLS[host]
    if host == "copilot" and "toolName" not in event:
        # VS Code's Local harness also loads .github/hooks/*.json and sends
        # its own snake_case payload; tool names then follow that host.
        names = None
    if not isinstance(tool, str):
        raise BadEvent("missing tool name")
    if names is not None and tool not in names:
        return None
    if not isinstance(args, dict):
        return None
    command = args.get("command")
    return command if isinstance(command, str) else None


def deny(host: str, reason: str) -> dict:
    if host in {"claude", "codex", "vscode"}:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    if host == "gemini":
        return {"decision": "deny", "reason": reason}
    if host == "cursor":
        return {"permission": "deny", "user_message": reason, "agent_message": reason}
    return {"permissionDecision": "deny", "permissionDecisionReason": reason}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--host", required=True, choices=sorted(SHELL_TOOLS))
    parser.add_argument("--deny", action="append", default=[])
    args = parser.parse_args(argv)
    rules = {p: p for p in args.deny} if args.deny else DEFAULT_DENY
    patterns = {label: re.compile(regex) for label, regex in rules.items()}
    try:
        command = shell_command(args.host, read_event())
    except BadEvent as error:
        print(f"guard_shell: {error}; blocking", file=sys.stderr)
        return 2
    if command is None:
        return 0
    for label, pattern in patterns.items():
        if pattern.search(command):
            reason = f"Blocked by guard_shell ({label}): {command[:200]}"
            print(json.dumps(deny(args.host, reason)))
            return 0
    if args.host == "gemini":
        print("{}")  # stdout must be exactly one JSON object on exit 0
    elif args.host == "cursor":
        # Cursor counts "no output" as a hook failure, which blocks when the
        # entry sets failClosed, so the allow path answers explicitly.
        print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
