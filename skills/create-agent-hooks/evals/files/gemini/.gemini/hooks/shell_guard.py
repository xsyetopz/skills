"""BeforeTool: no opinion unless the command deletes the repository root."""
import json
import sys

payload = json.load(sys.stdin)
command = payload.get("tool_input", {}).get("command", "")
if "rm -rf /" in command:
    print(json.dumps({"decision": "deny", "reason": "Refusing to delete the filesystem root."}))
else:
    print("{}")
