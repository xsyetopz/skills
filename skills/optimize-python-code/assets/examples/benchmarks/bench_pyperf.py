#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyperf==2.10.0"]
# ///
"""pyperf keeps its complete native CLI; --variant is forwarded to workers."""

import importlib.util
from pathlib import Path

import pyperf

_module_path = Path(__file__).resolve().parents[1] / "comparisons/pairs.py"
_spec = importlib.util.spec_from_file_location("pairs", _module_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_module_path}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
PAIRS = _module.PAIRS
workload = _module.workload
verify = _module.verify


def worker_args(command, args):
    command.extend(("--variant", args.variant))


def main():
    verify()  # Independent fixture expectations, outside measured calls.
    runner = pyperf.Runner(add_cmdline_args=worker_args)
    runner.argparser.add_argument(
        "--variant", choices=("baseline", "candidate"), required=True
    )
    args = runner.parse_args()
    for case in (1, 3, 7):
        for size in (16, 256, 4096):
            inputs = workload(case, size)
            baseline, candidate = PAIRS[case - 1]
            if baseline(*inputs) != candidate(*inputs):
                raise RuntimeError(
                    "benchmark implementations disagree before measurement"
                )
            function = candidate if args.variant == "candidate" else baseline
            runner.bench_func(f"case_{case}/n_{size}", function, *inputs)


if __name__ == "__main__":
    main()
