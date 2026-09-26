"""Oracle helpers shared by every construct module.

A check raises CheckError on the first mismatch so main.py exits nonzero and
names the failing construct. Benefit checks use deterministic counters
(tracemalloc peak bytes, executed bytecode instructions, Python calls,
comparison calls) wherever the cost is visible to Python; CPU-time ratios are
used only where the gap is asymptotic (quadratic versus linear).
"""

import dis
import gc
import sys
import time
import tracemalloc
from collections.abc import Callable
from types import CodeType
from typing import Any

COUNT = 0


class CheckError(AssertionError):
    pass


def _tick() -> None:
    global COUNT
    COUNT += 1


def equal(construct: str, expected: object, actual: object) -> None:
    _tick()
    if expected != actual:
        raise CheckError(f"{construct}: expected {expected!r}, got {actual!r}")


def _fmt(value: float) -> str:
    return f"{value:,}" if isinstance(value, int) else f"{value:.6g}"


def fewer(construct: str, metric: str, before: float, after: float) -> None:
    """Assert that the candidate's metric value is strictly below baseline."""
    _tick()
    print(f"METRIC {construct} {metric}: {_fmt(before)} -> {_fmt(after)}")
    if not after < before:
        raise CheckError(f"{construct}: {metric} {after} is not below {before}")


def more(construct: str, metric: str, before: float, after: float) -> None:
    """Assert that the candidate's metric value is strictly above baseline."""
    _tick()
    print(f"METRIC {construct} {metric}: {_fmt(before)} -> {_fmt(after)}")
    if not after > before:
        raise CheckError(f"{construct}: {metric} {after} is not above {before}")


def peak_bytes(action: Callable[[], object]) -> int:
    """Peak traced Python allocation of one call, after one warmup call."""
    action()
    gc.collect()
    tracemalloc.start()
    try:
        action()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def cpu_seconds(action: Callable[[], object], repeat: int = 3) -> float:
    """Minimum process CPU time over `repeat` calls (timeit's min rule)."""
    best = float("inf")
    for _ in range(repeat):
        start = time.process_time()
        action()
        best = min(best, time.process_time() - start)
    return best


def at_least_times_faster(
    construct: str,
    factor: float,
    baseline: Callable[[], object],
    candidate: Callable[[], object],
) -> None:
    """For asymptotic gaps only: baseline CPU >= factor * candidate CPU."""
    _tick()
    slow = cpu_seconds(baseline)
    fast = cpu_seconds(candidate)
    print(f"METRIC {construct} cpu s: {slow:.6f} -> {fast:.6f}")
    if slow < factor * max(fast, 1e-6):
        raise CheckError(f"{construct}: not {factor}x faster")


def _free_tool_id() -> int:
    if sys.version_info < (3, 12):
        raise CheckError("sys.monitoring requires Python 3.12+")
    for tool in range(6):
        if sys.monitoring.get_tool(tool) is None:
            return tool
    raise CheckError("no free sys.monitoring tool id")


def executed_ops(
    action: Callable[[], object], prefixes: tuple[str, ...]
) -> int:
    """Count executed instructions whose base opname starts with a prefix.

    Uses sys.monitoring INSTRUCTION events (Python 3.12+). A prefix of ""
    counts every executed instruction.
    """
    if sys.version_info < (3, 12):
        raise CheckError("sys.monitoring requires Python 3.12+")
    mon = sys.monitoring
    tool = _free_tool_id()
    names: dict[CodeType, dict[int, str]] = {}
    count = 0

    def on_instruction(code: CodeType, offset: int) -> None:
        nonlocal count
        table = names.get(code)
        if table is None:
            table = {i.offset: i.opname for i in dis.get_instructions(code)}
            names[code] = table
        if table.get(offset, "").startswith(prefixes):
            count += 1

    action()
    mon.use_tool_id(tool, "construct-check")
    try:
        mon.register_callback(tool, mon.events.INSTRUCTION, on_instruction)
        mon.set_events(tool, mon.events.INSTRUCTION)
        action()
    finally:
        mon.set_events(tool, mon.events.NO_EVENTS)
        mon.free_tool_id(tool)
    return count


def python_calls(action: Callable[[], object]) -> int:
    """Count Python function starts (PY_START) during one call."""
    if sys.version_info < (3, 12):
        raise CheckError("sys.monitoring requires Python 3.12+")
    mon = sys.monitoring
    tool = _free_tool_id()
    count = 0

    def on_start(code: CodeType, offset: int) -> None:
        nonlocal count
        count += 1

    action()
    mon.use_tool_id(tool, "construct-check")
    try:
        mon.register_callback(tool, mon.events.PY_START, on_start)
        mon.set_events(tool, mon.events.PY_START)
        action()
    finally:
        mon.set_events(tool, mon.events.NO_EVENTS)
        mon.free_tool_id(tool)
    return count - 1  # exclude the `action` wrapper itself


class Probe:
    """Hashable value that counts ==, <, and <= calls on the class."""

    calls = 0
    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        Probe.calls += 1
        return isinstance(other, Probe) and self.value == other.value

    def __lt__(self, other: "Probe") -> bool:
        Probe.calls += 1
        return self.value < other.value

    def __le__(self, other: "Probe") -> bool:
        Probe.calls += 1
        return self.value <= other.value

    def __repr__(self) -> str:
        return f"Probe({self.value!r})"


def comparisons(action: Callable[[], object]) -> int:
    Probe.calls = 0
    action()
    return Probe.calls
