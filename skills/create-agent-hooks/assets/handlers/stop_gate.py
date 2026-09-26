#!/usr/bin/env python3
"""Stop hook: keep the agent working until a check command passes.

For Claude Code and Codex, whose Stop events share the decision shape
{"decision": "block", "reason": ...}. The check runs with the event's
cwd. When stop_hook_active is true the agent is already continuing
because of a Stop hook, so the gate lets it stop instead of looping.

Usage: stop_gate.py --check "python3 -m unittest -q" [--timeout 120]
Exit status: 0 always for a valid event (the JSON carries the decision);
2 with a reason on stderr for an invalid event.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys

LIMIT = 1024 * 1024
TAIL = 2000  # characters of check output passed back to the agent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", required=True, help="command, one string")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
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
    try:
        result = subprocess.run(
            shlex.split(args.check),
            cwd=event.get("cwd") or None,
            capture_output=True,
            text=True,
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
