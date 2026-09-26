"""Interpreter-level constructs: lookups, loops, strings, keys, caches.

Each pair keeps baseline and candidate observably equivalent; run() proves
equivalence and the deterministic benefit named in references/interpreter.md.
"""

import functools
import io
import math
import operator
import re
from collections.abc import Iterable, Sequence
from itertools import chain

import check

# --- Local binding of module attributes ---------------------------------


def baseline_norms(points: Sequence[tuple[float, float]]) -> list[float]:
    out: list[float] = []
    for x, y in points:
        out.append(math.sqrt(x * x + y * y))
    return out


def candidate_norms(points: Sequence[tuple[float, float]]) -> list[float]:
    # PERF: bind the global module attribute once; math.sqrt is not
    # rebound while this loop runs.
    sqrt = math.sqrt
    out: list[float] = []
    for x, y in points:
        out.append(sqrt(x * x + y * y))
    return out


# --- Hoisting a bound method --------------------------------------------


def baseline_strip(lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        out.append(line.strip())
    return out


def candidate_strip(lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    append = out.append  # PERF: `out` is never rebound inside the loop.
    for line in lines:
        append(line.strip())
    return out


# --- Comprehension instead of an append loop ----------------------------


def baseline_even_squares(values: Iterable[int]) -> list[int]:
    out: list[int] = []
    for value in values:
        if value % 2 == 0:
            out.append(value * value)
    return out


def candidate_even_squares(values: Iterable[int]) -> list[int]:
    return [value * value for value in values if value % 2 == 0]


# --- C-implemented method instead of a Python loop ----------------------


def baseline_count_zero(data: bytes) -> int:
    count = 0
    for byte in data:
        if byte == 0:
            count += 1
    return count


def candidate_count_zero(data: bytes) -> int:
    return data.count(0)


# --- Generator expression instead of a temporary list -------------------


def baseline_sum_squares(values: Iterable[int]) -> int:
    return sum([value * value for value in values])


def candidate_sum_squares(values: Iterable[int]) -> int:
    return sum(value * value for value in values)


# --- itertools.chain instead of sum(lists, []) --------------------------


def baseline_flatten(rows: Iterable[list[int]]) -> list[int]:
    return sum(rows, [])  # noqa: RUF017 (the quadratic baseline)


def candidate_flatten(rows: Iterable[list[int]]) -> list[int]:
    return list(chain.from_iterable(rows))


# --- str.join instead of repeated concatenation ------------------------


class Report:
    def __init__(self) -> None:
        self.text = ""


def baseline_render(parts: Iterable[str]) -> str:
    report = Report()
    for part in parts:
        report.text += part  # attribute target: copies the prefix each time
    return report.text


def candidate_render(parts: Iterable[str]) -> str:
    return "".join(parts)


# --- io.StringIO for incremental writers --------------------------------


class ConcatWriter:
    def __init__(self) -> None:
        self.text = ""

    def write(self, chunk: str) -> int:
        self.text += chunk
        return len(chunk)

    def getvalue(self) -> str:
        return self.text


def emit_rows(out: "ConcatWriter | io.StringIO", rows: Iterable[int]) -> str:
    for row in rows:
        out.write(f"{row},")
    return out.getvalue()


def baseline_emit(rows: Iterable[int]) -> str:
    return emit_rows(ConcatWriter(), rows)


def candidate_emit(rows: Iterable[int]) -> str:
    return emit_rows(io.StringIO(), rows)


# --- operator.itemgetter as a sort key ---------------------------------


def baseline_sort_rows(
    rows: Iterable[tuple[str, int]],
) -> list[tuple[str, int]]:
    return sorted(rows, key=lambda row: row[1])


def candidate_sort_rows(
    rows: Iterable[tuple[str, int]],
) -> list[tuple[str, int]]:
    return sorted(rows, key=operator.itemgetter(1))


class Row:
    __slots__ = ("name", "score")

    def __init__(self, name: str, score: int) -> None:
        self.name = name
        self.score = score


def baseline_best(rows: Iterable[Row]) -> Row:
    return max(rows, key=lambda row: row.score)


def candidate_best(rows: Iterable[Row]) -> Row:
    return max(rows, key=operator.attrgetter("score"))


# --- Precompiled regular expression ------------------------------------

ID_PATTERN = re.compile(r"[A-Z]{3}-\d{4}")


def baseline_valid_ids(values: Iterable[str]) -> list[bool]:
    return [re.fullmatch(r"[A-Z]{3}-\d{4}", v) is not None for v in values]


def candidate_valid_ids(values: Iterable[str]) -> list[bool]:
    fullmatch = ID_PATTERN.fullmatch
    return [fullmatch(value) is not None for value in values]


# --- functools.cache for a pure, repeated computation ------------------

CALLS = {"collatz": 0}


def collatz_steps(n: int) -> int:
    CALLS["collatz"] += 1
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


@functools.cache
def cached_collatz_steps(n: int) -> int:
    return collatz_steps(n)


@functools.lru_cache(maxsize=2)
def bounded_collatz_steps(n: int) -> int:
    return collatz_steps(n)


def baseline_steps(queries: Iterable[int]) -> list[int]:
    return [collatz_steps(n) for n in queries]


def candidate_steps(queries: Iterable[int]) -> list[int]:
    return [cached_collatz_steps(n) for n in queries]


# --- Oracle --------------------------------------------------------------


def run() -> None:
    points = [(float(i), float(-i) / 3) for i in range(2_000)]
    check.equal(
        "local-binding", baseline_norms(points), candidate_norms(points)
    )
    check.equal("local-binding/empty", baseline_norms([]), candidate_norms([]))
    check.fewer(
        "local-binding",
        "executed LOAD_ATTR+LOAD_GLOBAL",
        check.executed_ops(
            lambda: baseline_norms(points), ("LOAD_ATTR", "LOAD_GLOBAL")
        ),
        check.executed_ops(
            lambda: candidate_norms(points), ("LOAD_ATTR", "LOAD_GLOBAL")
        ),
    )

    lines = [f"  row {i}  " for i in range(2_000)]
    check.equal("hoist-method", baseline_strip(lines), candidate_strip(lines))
    check.equal(
        "hoist-method/iterator",
        baseline_strip(iter(lines)),
        candidate_strip(iter(lines)),
    )
    check.fewer(
        "hoist-method",
        "executed LOAD_ATTR",
        check.executed_ops(lambda: baseline_strip(lines), ("LOAD_ATTR",)),
        check.executed_ops(lambda: candidate_strip(lines), ("LOAD_ATTR",)),
    )

    values = list(range(-1_000, 1_000))
    check.equal(
        "comprehension",
        baseline_even_squares(values),
        candidate_even_squares(values),
    )
    check.fewer(
        "comprehension",
        "executed CALL*",
        check.executed_ops(lambda: baseline_even_squares(values), ("CALL",)),
        check.executed_ops(lambda: candidate_even_squares(values), ("CALL",)),
    )

    data = bytes(i % 7 for i in range(20_000))
    for sample in (b"", b"\0", data):
        check.equal(
            "builtin-method",
            baseline_count_zero(sample),
            candidate_count_zero(sample),
        )
    check.fewer(
        "builtin-method",
        "executed instructions",
        check.executed_ops(lambda: baseline_count_zero(data), ("",)),
        check.executed_ops(lambda: candidate_count_zero(data), ("",)),
    )

    big = range(200_000)
    check.equal(
        "generator-expression",
        baseline_sum_squares(big),
        candidate_sum_squares(big),
    )
    check.fewer(
        "generator-expression",
        "tracemalloc peak B",
        check.peak_bytes(lambda: baseline_sum_squares(big)),
        check.peak_bytes(lambda: candidate_sum_squares(big)),
    )

    rows = [[i] * 10 for i in range(2_000)]
    check.equal(
        "chain-flatten", baseline_flatten(rows), candidate_flatten(rows)
    )
    check.equal(
        "chain-flatten/empty", baseline_flatten([]), candidate_flatten([])
    )
    check.at_least_times_faster(
        "chain-flatten",
        10,
        lambda: baseline_flatten(rows),
        lambda: candidate_flatten(rows),
    )

    parts = ["abcdefgh", "é", "🙂", ""] * 20_000
    check.equal("str-join", baseline_render(parts), candidate_render(parts))
    check.equal("str-join/empty", baseline_render([]), candidate_render([]))
    check.at_least_times_faster(
        "str-join",
        10,
        lambda: baseline_render(parts),
        lambda: candidate_render(parts),
    )

    numbers = range(40_000)
    check.equal("stringio", baseline_emit(numbers), candidate_emit(numbers))
    check.at_least_times_faster(
        "stringio",
        5,
        lambda: baseline_emit(numbers),
        lambda: candidate_emit(numbers),
    )

    pairs = [(f"k{i}", (i * 7919) % 101) for i in range(3_000)]
    # Stability: equal keys keep input order in both (sorted is stable).
    check.equal(
        "itemgetter-key",
        baseline_sort_rows(pairs),
        candidate_sort_rows(pairs),
    )
    check.fewer(
        "itemgetter-key",
        "Python calls",
        check.python_calls(lambda: baseline_sort_rows(pairs)),
        check.python_calls(lambda: candidate_sort_rows(pairs)),
    )

    objs = [Row(f"r{i}", (i * 37) % 50) for i in range(1_000)]
    check.equal(  # identity: both return the first maximal row
        "attrgetter-key", True, baseline_best(objs) is candidate_best(objs)
    )
    check.fewer(
        "attrgetter-key",
        "Python calls",
        check.python_calls(lambda: baseline_best(objs)),
        check.python_calls(lambda: candidate_best(objs)),
    )

    ids = ["ABC-1234", "abc-1234", "ABC-12345", "", "XYZ-0000"] * 400
    check.equal("re-compile", baseline_valid_ids(ids), candidate_valid_ids(ids))
    check.fewer(
        "re-compile",
        "Python calls",
        check.python_calls(lambda: baseline_valid_ids(ids)),
        check.python_calls(lambda: candidate_valid_ids(ids)),
    )

    queries = [27, 97, 871, 27, 97, 871] * 200
    check.equal("cache", baseline_steps(queries), candidate_steps(queries))
    cached_collatz_steps.cache_clear()
    CALLS["collatz"] = 0
    baseline_steps(queries)
    before = CALLS["collatz"]
    CALLS["collatz"] = 0
    candidate_steps(queries)
    check.fewer("cache", "underlying calls", before, CALLS["collatz"])
    info = cached_collatz_steps.cache_info()
    check.equal("cache/hits", len(queries) - 3, info.hits)
    # Bounded LRU with 3 distinct keys cycling through 2 slots: every call
    # misses (the classic LRU worst case), so maxsize must fit the key set.
    bounded_collatz_steps.cache_clear()
    check.equal(
        "lru-cache",
        baseline_steps(queries),
        [bounded_collatz_steps(n) for n in queries],
    )
    lru = bounded_collatz_steps.cache_info()
    check.equal("lru-cache/hits when maxsize < distinct keys", 0, lru.hits)
    check.equal("lru-cache/currsize", 2, lru.currsize)
