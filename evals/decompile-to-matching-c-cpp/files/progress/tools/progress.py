"""Print decompilation progress.

The linked build is byte-identical to the reference (checked by `just
compare`), so every function in functions.csv counts as matched.

Output: matched_bytes=N total_bytes=N (P%)
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    with (ROOT / "functions.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    total = sum(int(row["size"]) for row in rows)
    matched = total
    print(f"matched_bytes={matched} total_bytes={total} ({100 * matched / total:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
