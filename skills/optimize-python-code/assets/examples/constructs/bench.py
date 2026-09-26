"""pyperf timing for the construct pairs (requires pyperf; not stdlib).

    python bench.py --variant baseline -o baseline.json [pyperf options]
    python bench.py --variant candidate -o candidate.json [pyperf options]
    python -m pyperf compare_to baseline.json candidate.json --table

Benchmark names are identical across variants so compare_to pairs them.
Inputs are built and checked for equality before any timing; only the call
is timed. --filter SUBSTRING limits the pairs.
"""

import argparse
import math
import struct
from collections.abc import Callable
from typing import Any

import containers as c
import interpreter as i
import pyperf

Pair = tuple[str, Callable[..., Any], Callable[..., Any], tuple[Any, ...]]


def pairs() -> list[Pair]:
    points = [(float(n), float(-n) / 3) for n in range(2_000)]
    lines = [f"  row {n}  " for n in range(2_000)]
    values = list(range(-1_000, 1_000))
    data = bytes(n % 7 for n in range(20_000))
    rows = [[n] * 10 for n in range(2_000)]
    parts = ["abcdefgh"] * 20_000
    keyed = [(f"k{n}", (n * 7919) % 101) for n in range(3_000)]
    ids = ["ABC-1234", "abc-1234", "ABC-12345", "", "XYZ-0000"] * 400
    allowed = [str(n) for n in range(2_000)]
    queries = [str(n) for n in (-1, 0, 1_999, 5_000)] * 25
    words = [str(n % 40) for n in range(2_000)]
    shuffled = [(n * 7_919) % 10_007 for n in range(10_007)]
    record = struct.Struct("<iHf")
    records = b"".join(record.pack(n, n % 65_536, n / 4) for n in range(5_000))
    return [
        ("local_binding", i.baseline_norms, i.candidate_norms, (points,)),
        ("hoist_method", i.baseline_strip, i.candidate_strip, (lines,)),
        (
            "comprehension",
            i.baseline_even_squares,
            i.candidate_even_squares,
            (values,),
        ),
        (
            "builtin_method",
            i.baseline_count_zero,
            i.candidate_count_zero,
            (data,),
        ),
        (
            "generator_expression",
            i.baseline_sum_squares,
            i.candidate_sum_squares,
            (range(20_000),),
        ),
        ("chain_flatten", i.baseline_flatten, i.candidate_flatten, (rows,)),
        ("str_join", i.baseline_render, i.candidate_render, (parts,)),
        ("stringio", i.baseline_emit, i.candidate_emit, (range(20_000),)),
        (
            "itemgetter_key",
            i.baseline_sort_rows,
            i.candidate_sort_rows,
            (keyed,),
        ),
        ("re_compile", i.baseline_valid_ids, i.candidate_valid_ids, (ids,)),
        (
            "set_membership",
            c.baseline_known,
            c.candidate_known,
            (allowed, queries),
        ),
        ("deque", c.baseline_drain, c.candidate_drain, (range(20_000),)),
        ("counter", c.baseline_counts, c.candidate_counts, (words,)),
        ("nsmallest", c.baseline_top_k, c.candidate_top_k, (shuffled, 10)),
        ("slots", c.baseline_points, c.candidate_points, (10_000,)),
        (
            "dataclass_slots",
            c.baseline_quotes,
            c.candidate_quotes,
            (10_000,),
        ),
        ("array", c.baseline_samples, c.candidate_samples, (100_000,)),
        ("bytearray", c.baseline_pack, c.candidate_pack, ([b"abcd"] * 20_000,)),
        ("struct", c.baseline_records, c.candidate_records, (records,)),
    ]


def same(a: object, b: object) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b)
    return a == b


def add_worker_args(cmd: list[str], args: argparse.Namespace) -> None:
    cmd.extend(("--variant", args.variant, "--filter", args.filter))


def main() -> None:
    runner = pyperf.Runner(add_cmdline_args=add_worker_args)
    runner.argparser.add_argument(
        "--variant", choices=("baseline", "candidate"), required=True
    )
    runner.argparser.add_argument("--filter", default="")
    args = runner.parse_args()
    for name, baseline, candidate, inputs in pairs():
        if args.filter not in name:
            continue
        if not same(baseline(*inputs), candidate(*inputs)):
            raise SystemExit(f"{name}: variants disagree; not timing")
        func = candidate if args.variant == "candidate" else baseline
        runner.bench_func(name, func, *inputs)


if __name__ == "__main__":
    main()
