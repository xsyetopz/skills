"""Write a 400-row CSV where row 287 has a quoted comma (the trigger)."""

import sys

rows = ["id,name,city"]
for i in range(1, 401):
    name = '"Smith, Jr."' if i == 287 else f"person{i}"
    rows.append(f"{i},{name},city{i % 7}")
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    handle.write("\n".join(rows) + "\n")
