"""Fail if library code under the given directory calls print(); use logging."""
import pathlib
import re
import sys

bad = [f"{p}:{n}" for p in pathlib.Path(sys.argv[1]).rglob("*.py") if not p.name.startswith("_version")
       for n, line in enumerate(p.read_text().splitlines(), 1) if re.match(r"\s*print\(", line)]
print("\n".join(bad) or "no print() calls")
sys.exit(1 if bad else 0)
