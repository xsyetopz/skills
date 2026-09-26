"""Measurement constructs: timeit, cProfile, tracemalloc, sys.monitoring,
-X importtime, and the differential oracle. See references/measurement.md.
"""

import cProfile
import io
import linecache
import os
import pstats
import subprocess
import sys
import tempfile
import timeit
import tracemalloc
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path
from types import CodeType

import check

HERE = Path(__file__).resolve().parent

# --- Workload used by the profiler examples -----------------------------


def tokenize(line: str) -> list[str]:
    return line.split()


def normalize(token: str) -> str:
    return token.strip(".,").lower()


def word_counts(lines: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        for token in tokenize(line):
            word = normalize(token)
            counts[word] = counts.get(word, 0) + 1
    return counts


LINES = ["The quick brown fox, the lazy dog."] * 500

# --- timeit ----------------------------------------------------------------


def timeit_min_seconds(stmt: Callable[[], object]) -> float:
    timer = timeit.Timer(stmt)
    loops, _ = timer.autorange()  # loops so one repeat lasts >= 0.2 s
    runs = timer.repeat(repeat=5, number=loops)
    return min(runs) / loops  # seconds per call; report min, not mean


# --- cProfile + pstats ---------------------------------------------------


def profile_calls(action: Callable[[], object]) -> dict[str, int]:
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        action()
    finally:
        profiler.disable()
    report = io.StringIO()
    stats = pstats.Stats(profiler, stream=report)
    stats.sort_stats("cumulative").print_stats(8)
    # stats.stats maps (file, line, name) -> (cc, nc, tt, ct, callers)
    raw: dict[tuple[str, int, str], tuple[int, ...]]
    raw = stats.stats  # type: ignore[attr-defined]
    return {name: row[1] for (_, _, name), row in raw.items()}


# --- tracemalloc snapshot diff ------------------------------------------


def build_index(n: int) -> dict[int, str]:
    return {i: f"value-{i}" for i in range(n)}  # the allocating line


def top_allocating_line(action: Callable[[], object]) -> tuple[str, str]:
    tracemalloc.start()
    try:
        before = tracemalloc.take_snapshot()
        kept = action()
        after = tracemalloc.take_snapshot()
    finally:
        tracemalloc.stop()
    del kept
    filters = [tracemalloc.Filter(True, __file__)]
    diff = after.filter_traces(filters).compare_to(
        before.filter_traces(filters), "lineno"
    )
    frame = diff[0].traceback[0]
    line = linecache.getline(frame.filename, frame.lineno).strip()
    return Path(frame.filename).name, line


# --- sys.monitoring call counter (3.12+) --------------------------------


def monitor_calls(action: Callable[[], object]) -> Counter[str]:
    """Count Python function starts by qualified name with PY_START."""
    if sys.version_info < (3, 12):
        raise check.CheckError("sys.monitoring requires Python 3.12+")
    mon = sys.monitoring
    # cProfile holds PROFILER_ID (2) while enabled in 3.12+, so pick a free id.
    tool = next(t for t in range(6) if mon.get_tool(t) is None)
    counts: Counter[str] = Counter()

    def on_start(code: CodeType, offset: int) -> None:
        counts[code.co_qualname] += 1

    mon.use_tool_id(tool, "call-counter")
    try:
        mon.register_callback(tool, mon.events.PY_START, on_start)
        mon.set_events(tool, mon.events.PY_START)
        action()
    finally:
        mon.set_events(tool, mon.events.NO_EVENTS)
        mon.free_tool_id(tool)
    return counts


# --- -X importtime ---------------------------------------------------------


def import_times(module: str, cache_dir: str) -> dict[str, int]:
    """Cumulative import microseconds per module from -X importtime.

    Bytecode caches go to `cache_dir` (-X pycache_prefix), so the source tree
    stays clean and compile time is excluded after the first run.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            f"pycache_prefix={cache_dir}",
            "-X",
            "importtime",
            "-c",
            f"import {module}",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=HERE,
        # Allow the cache under cache_dir even when the caller disabled
        # bytecode writing, so warm runs exclude compile time.
        env={
            k: v
            for k, v in os.environ.items()
            if k != "PYTHONDONTWRITEBYTECODE"
        },
    )
    times: dict[str, int] = {}
    for line in result.stderr.splitlines():
        # "import time: self [us] | cumulative | imported package"
        if not line.startswith("import time:") or "[us]" in line:
            continue
        _self, cumulative, name = line.split(":", 1)[1].split("|")
        times[name.strip()] = int(cumulative)
    return times


def best_import(module: str, cache_dir: str) -> dict[str, int]:
    import_times(module, cache_dir)  # warm the bytecode cache
    runs = [import_times(module, cache_dir) for _ in range(5)]
    return min(runs, key=lambda times: times[module])


# --- Differential oracle with semantic traps ----------------------------


def reference_unique(values: Iterable[int]) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def good_unique(values: Iterable[int]) -> list[int]:
    return list(dict.fromkeys(values))  # keeps first-seen order


def bad_unique_order(values: Iterable[int]) -> list[int]:
    return list(set(values))  # loses first-seen order


def bad_unique_twice(values: Iterable[int]) -> list[int]:
    if not list(values):  # consumes a one-shot iterator
        return []
    return list(dict.fromkeys(values))


def differential(
    name: str,
    baseline: Callable[[Iterable[int]], list[int]],
    candidate: Callable[[Iterable[int]], list[int]],
) -> None:
    cases: list[list[int]] = [[], [0], [3, 1, 3, 2, 1], [5, -5, 0, 5]]
    for case in cases:
        check.equal(name, baseline(list(case)), candidate(list(case)))
        check.equal(f"{name}/iter", baseline(iter(case)), candidate(iter(case)))
        check.equal(
            f"{name}/tuple", baseline(tuple(case)), candidate(tuple(case))
        )


def rejects(name: str, candidate: Callable[[Iterable[int]], list[int]]) -> None:
    try:
        differential(name, reference_unique, candidate)
    except check.CheckError as error:
        print(f"ORACLE rejected {name}: {error}")
        return
    raise check.CheckError(f"oracle accepted broken candidate {name}")


# --- Oracle ----------------------------------------------------------------


def run() -> None:
    expected = word_counts(LINES)
    per_call = timeit_min_seconds(lambda: word_counts(LINES))
    print(f"METRIC timeit word_counts: {per_call * 1e6:.1f} us/call (min of 5)")
    check.equal("timeit/positive", True, per_call > 0)

    calls = profile_calls(lambda: word_counts(LINES))
    check.equal("cprofile/tokenize ncalls", len(LINES), calls["tokenize"])
    check.equal(
        "cprofile/normalize ncalls", sum(expected.values()), calls["normalize"]
    )

    filename, line = top_allocating_line(lambda: build_index(20_000))
    check.equal("tracemalloc-diff/file", "measurement.py", filename)
    check.equal(
        "tracemalloc-diff/line",
        'return {i: f"value-{i}" for i in range(n)}  # the allocating line',
        line,
    )

    counts = monitor_calls(lambda: word_counts(LINES))
    check.equal("sys.monitoring/tokenize", len(LINES), counts["tokenize"])
    check.equal(
        "sys.monitoring/normalize", calls["normalize"], counts["normalize"]
    )

    with tempfile.TemporaryDirectory() as cache_dir:
        eager = best_import("startup_eager", cache_dir)
        lazy = best_import("startup_lazy", cache_dir)
    check.equal("importtime/decimal imported", True, "decimal" in eager)
    check.equal("importtime/decimal deferred", False, "decimal" in lazy)
    check.fewer("importtime", "modules imported", len(eager), len(lazy))
    print(
        "METRIC importtime cumulative us, min of 5 (machine-specific): "
        f"{eager['startup_eager']} -> {lazy['startup_lazy']}"
    )

    differential("dict-fromkeys", reference_unique, good_unique)
    rejects("set-order", bad_unique_order)
    rejects("iterator-consumed", bad_unique_twice)
