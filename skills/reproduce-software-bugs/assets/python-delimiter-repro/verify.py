"""Accept only the documented parser failure; setup failure is not success."""

import subprocess
import sys
from pathlib import Path

reproducer = Path(__file__).with_name("repro.py")
try:
    result = subprocess.run(
        [sys.executable, str(reproducer)],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
except (OSError, subprocess.TimeoutExpired) as exc:
    raise SystemExit(f"reproducer could not run: {exc}") from exc
if (
    result.returncode != 1
    or "ValueError: too many values to unpack" not in result.stderr
):
    raise SystemExit(
        f"wrong failure or unexpected success:\n{result.stdout}\n{result.stderr}"
    )
print("Reproduced the documented delimiter parsing failure.")
