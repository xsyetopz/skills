"""Run checked-in stdlib unit-test files without requiring Python packages."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    tests = sorted(Path("skills").glob("**/test_*.py"))
    skipped = {
        Path(
            "skills/sublime-plugin-development/assets/package-template/"
            "tests/test_commands.py"
        ): "requires the Sublime Text host",
    }
    for test in tests:
        if test in skipped:
            print(f"SKIP {test}: {skipped[test]}")
            continue
        print(f"RUN  {test}", flush=True)
        result = subprocess.run([sys.executable, str(test)], check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
