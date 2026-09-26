"""SessionStart: tell Gemini which branch and ticket it is working on."""
import json
import subprocess

branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
print(json.dumps({"hookSpecificOutput": {"additionalContext": f"Current branch: {branch or 'unknown'}"}}))
