"""Naive CSV reader with a bug: it splits on every comma, so a quoted field
containing a comma produces too many fields."""

import sys


def read_rows(text: str) -> list[list[str]]:
    lines = text.splitlines()
    header = lines[0].split(",")
    rows = []
    for number, line in enumerate(lines[1:], 2):
        fields = line.split(",")
        if len(fields) != len(header):
            raise ValueError(
                f"line {number}: expected {len(header)} fields, got {len(fields)}"
            )
        rows.append(fields)
    return rows


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        read_rows(handle.read())
