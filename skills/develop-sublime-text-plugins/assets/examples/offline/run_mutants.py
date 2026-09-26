"""Run both offline suites on the reference and on every mutant.

The reference must pass; each mutant must make its expected test fail.
Exit status 1 names the first surviving mutant or reference failure.

    python run_mutants.py            # with the current interpreter
    uv run --python 3.8 --no-project python run_mutants.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from variants import VARIANTS  # noqa: E402

SUITES = ("test_core.py", "test_adapter.py")
# Failure headers and the "Ran N tests" line have the same shape on 3.8
# and 3.14; per-test verbose lines do not (subTest output differs).
FAILED = re.compile(r"^(?:FAIL|ERROR): (test_\w+) ", re.M)
RAN = re.compile(r"^Ran (\d+) tests?", re.M)


def run(variant: str) -> Tuple[bool, List[str], int]:
    env = dict(os.environ, VARIANT=variant, PYTHONDONTWRITEBYTECODE="1")
    passed, failing, total = True, [], 0
    for suite in SUITES:
        proc = subprocess.run(
            [sys.executable, suite],
            cwd=str(HERE),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        ran = RAN.search(proc.stderr)
        total += int(ran.group(1)) if ran else 0
        failing += sorted(set(FAILED.findall(proc.stderr)))
        passed = passed and proc.returncode == 0
    return passed, failing, total


def main() -> int:
    print("python", sys.version.split()[0])
    ok, failing, total = run("")
    if not ok:
        print("FAIL reference:", ", ".join(failing) or "suite error")
        return 1
    print("reference: %d tests passed" % total)
    for name, variant in VARIANTS.items():
        ok, failing, _ = run(name)
        if ok or variant.expect not in failing:
            print("SURVIVED %s: expected %s to fail" % (name, variant.expect))
            return 1
        print(
            "killed %-22s %d failing, incl. %s" % (name, len(failing), variant.expect)
        )
    print("%d/%d mutants killed" % (len(VARIANTS), len(VARIANTS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
