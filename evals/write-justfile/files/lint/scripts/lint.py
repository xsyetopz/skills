"""Fail on unused-looking imports: `import X` where X never appears again."""
import re
import sys
from pathlib import Path

problems = []
for path in sorted(Path(sys.argv[1]).rglob("*.py")):
    text = path.read_text()
    for n, line in enumerate(text.splitlines(), 1):
        m = re.match(r"import (\w+)$", line)
        if m and len(re.findall(rf"\b{m.group(1)}\b", text)) == 1:
            problems.append(f"{path}:{n}: unused import {m.group(1)}")
print("\n".join(problems) or "lint: ok")
sys.exit(1 if problems else 0)
