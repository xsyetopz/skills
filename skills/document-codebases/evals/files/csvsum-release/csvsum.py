"""Sum a numeric column of a CSV file."""

import argparse
import csv
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="csvsum", description=__doc__)
    parser.add_argument("file", help="CSV file with a header row")
    parser.add_argument("-c", "--column", required=True, help="column name to sum")
    parser.add_argument("-d", "--delimiter", default=",", help="field delimiter")
    parser.add_argument(
        "-p", "--precision", type=int, help="round the total to this many decimals"
    )
    args = parser.parse_args(argv)
    total = 0.0
    with open(args.file, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter=args.delimiter):
            value = row.get(args.column)
            if value is None:
                parser.error(f"no column named {args.column!r}")
            if value.strip():
                total += float(value)
    print(f"{total:.{args.precision}f}" if args.precision is not None else f"{total:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
