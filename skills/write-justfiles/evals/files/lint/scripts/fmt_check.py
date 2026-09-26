"""Fail when a file has trailing whitespace or tabs."""
import sys
from pathlib import Path

bad = [f"{p}:{n}" for p in sorted(Path(sys.argv[1]).rglob("*.py"))
       for n, line in enumerate(p.read_text().splitlines(), 1) if line != line.rstrip() or "\t" in line]
print("\n".join(f"{b}: whitespace" for b in bad) or "format: ok")
sys.exit(1 if bad else 0)
