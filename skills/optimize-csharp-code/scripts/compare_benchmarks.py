#!/usr/bin/env python3
"""Compare complete BenchmarkDotNet-style CSV tables without guessing row identity.

Only duration metrics are supported. Every column must be named as an identity
column, the metric, or an explicitly ignored column. Exit 0: within threshold;
1: regression; 2: invalid or incomparable input. No files are modified.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

UNITS = {
    "ns": Decimal(1),
    "us": Decimal(1000),
    "µs": Decimal(1000),
    "μs": Decimal(1000),
    "ms": Decimal(1000000),
    "s": Decimal(1000000000),
}


class InputError(ValueError):
    """A comparison cannot be established from these inputs."""


def duration_ns(text: str, *, decimal: str = ".", unit: str | None = None) -> Decimal:
    """Parse a complete positive finite duration; reject guessing and grouping."""
    sep = re.escape(decimal)
    pattern = rf"\s*([+]?(?:[0-9]+(?:{sep}[0-9]+)?|{sep}[0-9]+)(?:[eE][+-]?[0-9]+)?)\s*([a-zµμ]+)?\s*"
    match = re.fullmatch(pattern, text)
    if not match:
        raise InputError(
            f"invalid duration {text!r}; use an ungrouped positive number and a supported unit"
        )
    suffix = match.group(2) or unit
    if suffix not in UNITS:
        raise InputError(
            f"unknown/missing duration unit in {text!r}; supported: ns, us, µs, μs, ms, s"
        )
    try:
        value = Decimal(match.group(1).replace(decimal, ".")) * UNITS[suffix]
    except (InvalidOperation, ArithmeticError) as exc:
        raise InputError(f"invalid numeric duration {text!r}") from exc
    if not value.is_finite() or value <= 0:
        raise InputError(f"duration must be finite and greater than zero: {text!r}")
    return value


def read_table(
    path: Path,
    keys: Sequence[str],
    metric: str,
    ignored: Sequence[str],
    *,
    delimiter: str = ",",
    decimal: str = ".",
    unit: str | None = None,
) -> dict[tuple[str, ...], Decimal]:
    rows: dict[tuple[str, ...], Decimal] = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter=delimiter, strict=True)
        header = next(reader, None)
        if not header or any(not item.strip() for item in header):
            raise InputError(f"{path}: missing or empty column header")
        if any(item != item.strip() for item in header):
            raise InputError(
                f"{path}: header whitespace is ambiguous; export canonical CSV headers"
            )
        if len(set(header)) != len(header):
            raise InputError(f"{path}: duplicate column headers")
        classified = set(keys) | {metric} | set(ignored)
        missing = classified - set(header)
        unknown = set(header) - classified
        if missing or unknown:
            raise InputError(
                f"{path}: missing declared columns={sorted(missing)}; "
                f"unclassified columns={sorted(unknown)}. Classify ALL columns with --keys/--ignore-columns."
            )
        indices = [header.index(key) for key in keys]
        metric_index = header.index(metric)
        for row in reader:
            line = reader.line_num
            if not row:  # CSV permits blank physical lines; not empty records.
                continue
            if len(row) != len(header):
                raise InputError(
                    f"{path}:{line}: expected {len(header)} cells, got {len(row)}"
                )
            identity = tuple(row[index] for index in indices)
            if any(not cell.strip() for cell in identity):
                raise InputError(
                    f"{path}:{line}: empty identity component {identity!r}"
                )
            if identity in rows:
                raise InputError(
                    f"{path}:{line}: duplicate identity {identity!r}; include every job/parameter in --keys"
                )
            try:
                rows[identity] = duration_ns(
                    row[metric_index], decimal=decimal, unit=unit
                )
            except InputError as exc:
                raise InputError(f"{path}:{line}: {exc}") from exc
    if not rows:
        raise InputError(f"{path}: no measurement rows")
    return rows


def compare(
    baseline: dict[tuple[str, ...], Decimal],
    candidate: dict[tuple[str, ...], Decimal],
    threshold: Decimal,
) -> list[tuple[tuple[str, ...], Decimal, Decimal, Decimal, bool]]:
    if not baseline or not candidate:
        raise InputError("both tables must contain measurements")
    if baseline.keys() != candidate.keys():
        raise InputError(
            f"identities differ; missing in candidate={sorted(baseline.keys() - candidate.keys())!r}; "
            f"new in candidate={sorted(candidate.keys() - baseline.keys())!r}"
        )
    if not threshold.is_finite() or threshold < 0:
        raise InputError("regression threshold must be finite and non-negative")
    results = []
    for key in sorted(baseline):
        before, after = baseline[key], candidate[key]
        if not before.is_finite() or not after.is_finite() or min(before, after) <= 0:
            raise InputError(f"invalid duration for {key!r}")
        change = (after / before - 1) * 100
        results.append((key, before, after, change, change > threshold))
    return results


def threshold_value(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("threshold must be a decimal number") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError("threshold must be finite and non-negative")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument(
        "--keys",
        nargs="+",
        required=True,
        help="ALL job/runtime/parameter identity column names",
    )
    parser.add_argument(
        "--metric", default="Mean", help="duration column (default: Mean)"
    )
    parser.add_argument(
        "--ignore-columns",
        nargs="*",
        default=[],
        help="explicitly unused columns, e.g. Error StdDev",
    )
    parser.add_argument("--max-regression-percent", type=threshold_value, required=True)
    parser.add_argument("--delimiter", default=",", choices=[",", ";", "\t"])
    parser.add_argument("--decimal", default=".", choices=[".", ","])
    parser.add_argument(
        "--unit",
        choices=list(UNITS),
        help="unit ONLY for cells with no suffix; no inference",
    )
    args = parser.parse_args(argv)
    classified = [*args.keys, args.metric, *args.ignore_columns]
    if len(classified) != len(set(classified)):
        parser.error("a column must be classified exactly once")
    if args.decimal == args.delimiter:
        parser.error(
            "decimal and delimiter must differ; use --delimiter ';' for decimal-comma exports"
        )
    try:
        kwargs = dict(
            keys=args.keys,
            metric=args.metric,
            ignored=args.ignore_columns,
            delimiter=args.delimiter,
            decimal=args.decimal,
            unit=args.unit,
        )
        baseline = read_table(args.baseline, **kwargs)
        candidate = read_table(args.candidate, **kwargs)
        results = compare(baseline, candidate, args.max_regression_percent)
    except (InputError, OSError, UnicodeError, csv.Error, ArithmeticError) as exc:
        print(f"comparison invalid: {exc}", file=sys.stderr)
        return 2
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(
        [*args.keys, "baseline_ns", "candidate_ns", "change_percent", "regression"]
    )
    for key, before, after, change, regression in results:
        writer.writerow(
            [
                *key,
                str(before),
                str(after),
                format(change, ".8g"),
                str(regression).lower(),
            ]
        )
    return int(any(row[-1] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
