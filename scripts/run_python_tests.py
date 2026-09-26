"""Run checked-in stdlib unit-test files without requiring Python packages."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    tests = sorted(
        test
        for test in [
            *Path("skills").glob("**/test_*.py"),
            *Path("scripts").glob("**/test_*.py"),
        ]
        # Eval fixtures carry tests that fail on purpose until a run fixes them.
        if "/evals/files/" not in test.as_posix()
    )
    # Tests import published packages and start child interpreters; neither
    # may leave __pycache__ directories inside skills/.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for test in tests:
        print(f"RUN  {test}", flush=True)
        result = subprocess.run([sys.executable, str(test)], check=False, env=env)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
