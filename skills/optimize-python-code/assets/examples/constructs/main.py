"""Run every construct oracle: python main.py [verify|MODULE...].

Exits nonzero on the first failed check. Timing belongs to bench.py (pyperf);
this runner asserts equivalence plus deterministic benefit metrics.
"""

import platform
import sys

import check
import concurrency
import containers
import interpreter
import measurement
import runtime

MODULES = {
    "measurement": measurement.run,
    "interpreter": interpreter.run,
    "containers": containers.run,
    "concurrency": concurrency.run,
    "runtime": runtime.run,
}


def main(argv: list[str]) -> int:
    names = [name for name in argv if name != "verify"] or list(MODULES)
    unknown = [name for name in names if name not in MODULES]
    if unknown:
        print(f"unknown module(s): {unknown}; use {list(MODULES)}")
        return 2
    print(f"python {sys.version.split()[0]} {platform.machine()}")
    for name in names:
        print(f"== {name}")
        MODULES[name]()
    print(f"PASSED {check.COUNT} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
