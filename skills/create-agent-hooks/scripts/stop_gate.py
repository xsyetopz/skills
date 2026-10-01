#!/usr/bin/env python3
"""Stop hook: keep the agent working until a check command passes.

For Claude Code and Codex, whose Stop events share the decision shape
{"decision": "block", "reason": ...}. The check runs with the event's
cwd. When stop_hook_active is true the agent is already continuing
because of a Stop hook, so the gate lets it stop instead of looping.

Usage: stop_gate.py --check "python3 -m unittest -q" [--timeout 120]
Exit status: 0 always for a valid event (the JSON carries the decision);
2 with a reason on stderr for an invalid event, or a --check that is empty
or has an unclosed quote.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys

LIMIT = 1024 * 1024
TAIL = 2000  # characters of check output passed back to the agent

EPILOG = """\
Exit status:
  0  always, for a valid Stop event (the JSON decision carries the
     check's outcome: block with a reason, or {} to let the agent stop)
  2  stdin is not a Stop event object, or --check is empty or has an
     unclosed quote (reason on stderr)

Examples:
  python3 stop_gate.py --check "python3 -m unittest -q" < stop-event.json
  python3 stop_gate.py --check "just test" --timeout 300 < stop-event.json
"""


def split_command(command: str, windows: bool = os.name == "nt") -> list[str]:
    """Split --check into words; raise ValueError on an unclosed quote.

    POSIX rules treat backslashes as escapes, which would turn
    `C:\\Python\\python.exe` into `C:Pythonpython.exe`, so Windows keeps
    backslashes and only strips the double quotes around a word.
    """
    if not windows:
        return shlex.split(command)
    words = shlex.split(command, posix=False)
    return [w[1:-1] if len(w) > 1 and w[0] == w[-1] == '"' else w for w in words]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check", required=True, help="command, one string")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    try:
        command = split_command(args.check)
    except ValueError as error:
        command, problem = [], f"has an unclosed quote ({error})"
    else:
        problem = "is empty"
    if not command:
        print(f"stop_gate: --check {problem}", file=sys.stderr)
        return 2
    raw = sys.stdin.buffer.read(LIMIT + 1)
    try:
        event = json.loads(raw.decode("utf-8")) if len(raw) <= LIMIT else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        event = None
    if not isinstance(event, dict) or event.get("hook_event_name") != "Stop":
        print("stop_gate: expected a Stop event object", file=sys.stderr)
        return 2
    if event.get("stop_hook_active") is True:
        print("{}")  # already continued once: let the agent stop
        return 0
    command[0] = shutil.which(command[0]) or command[0]  # finds npm.cmd on Windows
    try:
        result = subprocess.run(
            command,
            cwd=event.get("cwd") or None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        reason = f"`{args.check}` did not finish within {args.timeout:g}s."
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    except OSError as error:
        reason = f"`{args.check}` could not start: {error}"
        print(json.dumps({"decision": "block", "reason": reason}))
        return 0
    if result.returncode == 0:
        print("{}")
        return 0
    output = (result.stdout + result.stderr)[-TAIL:]
    reason = (
        f"`{args.check}` failed with exit {result.returncode}. "
        f"Fix the failures before finishing:\n{output}"
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
