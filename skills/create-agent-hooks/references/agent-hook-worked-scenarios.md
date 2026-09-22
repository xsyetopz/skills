# Worked scenarios for Agent Hook

## Safe structured pre-action validator

```python
#!/usr/bin/env python3
import json, pathlib, sys

payload = json.load(sys.stdin)
path_text = payload.get("path")
if not isinstance(path_text, str):
    print(json.dumps({"decision": "deny", "reason": "missing path"}))
    raise SystemExit(2)

root = pathlib.Path(payload["workspace_root"]).resolve()
target = (root / path_text).resolve()
if root not in target.parents and target != root:
    print(json.dumps({"decision": "deny", "reason": "path escapes workspace"}))
    raise SystemExit(2)

print(json.dumps({"decision": "allow"}))
```

Adapt field names and result shape only from the selected host's documentation.
Do not add `subprocess.run(payload["command"], shell=True)`.

## Rollback-safe configuration edit

Before:

```json
{ "hooks": [{ "event": "existing", "command": "./existing.sh" }] }
```

After adding one task-owned hook:

```json
{
  "hooks": [
    { "event": "existing", "command": "./existing.sh" },
    { "event": "preToolUse", "command": "./scripts/validate_tool.py" }
  ]
}
```

Rollback removes only the second entry and the script if the task created it. It
does not restore from a template or delete the whole file.

## Evidence boundary

A fixture test establishes parser and policy behavior. A host diagnostic or
controlled action establishes registration. Only a controlled action that the
host refuses establishes blocking for that event and version.
