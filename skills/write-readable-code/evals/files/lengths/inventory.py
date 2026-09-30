"""Stock report: parse a CSV export, check each row, and print a summary."""

import csv
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    quantity: int
    reorder_at: int


def parse_rows(lines):
    items = []
    for row in csv.DictReader(lines):
        items.append(
            Item(
                sku=row["sku"].strip(),
                name=row["name"].strip(),
                quantity=int(row["quantity"]),
                reorder_at=int(row["reorder_at"]),
            )
        )
    return items


def problems(items):
    found = []
    seen = set()
    for item in items:
        if item.sku in seen:
            found.append(f"{item.sku}: duplicate SKU")
        seen.add(item.sku)
        if item.quantity < 0:
            found.append(f"{item.sku}: negative quantity {item.quantity}")
        if item.reorder_at < 0:
            found.append(f"{item.sku}: negative reorder level")
    return found


def low_stock(items):
    return sorted(
        (item for item in items if item.quantity <= item.reorder_at),
        key=lambda item: item.quantity,
    )


def format_report(items, issues):
    lines = [f"{len(items)} items"]
    for item in low_stock(items):
        lines.append(f"reorder {item.sku} {item.name}: {item.quantity} left")
    for issue in issues:
        lines.append(f"problem {issue}")
    return "\n".join(lines)


def main(path):
    with open(path, newline="") as handle:
        items = parse_rows(handle)
    issues = problems(items)
    print(format_report(items, issues))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
