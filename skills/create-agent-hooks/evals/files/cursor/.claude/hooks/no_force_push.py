"""Claude Code PreToolUse hook: deny force pushes (except --force-with-lease)."""
import json
import re
import sys

try:
    payload = json.load(sys.stdin)
    command = payload["tool_input"]["command"]
except (ValueError, KeyError, TypeError):
    print("no_force_push: unreadable hook input", file=sys.stderr)
    sys.exit(2)

FORCE = re.compile(r"\bgit\s+push\b(?=.*(\s--force(?!-with-lease)\b|\s-[a-zA-Z]*f\b))")
if FORCE.search(command):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Force pushes are not allowed; use --force-with-lease.",
    }}))
