"""Container and buffer constructs; oracles in run().

See references/containers.md for the cards.
"""

import heapq
import struct
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import check
from check import Probe

# --- set membership instead of list membership --------------------------


def baseline_known(allowed: Sequence[object], queries: Iterable[object]):
    return [query in allowed for query in queries]


def candidate_known(allowed: Sequence[object], queries: Iterable[object]):
    members = set(allowed)  # requires hashable elements
    return [query in members for query in queries]


# --- deque as a FIFO queue -----------------------------------------------


def baseline_drain(values: Iterable[int]) -> list[int]:
    pending = list(values)
    out: list[int] = []
    while pending:
        out.append(pending.pop(0))
    return out


def candidate_drain(values: Iterable[int]) -> list[int]:
    pending = deque(values)
    out: list[int] = []
    while pending:
        out.append(pending.popleft())
    return out


# --- Counter instead of list.count per element --------------------------


def baseline_counts(values: Sequence[object]) -> dict[object, int]:
    return {value: values.count(value) for value in values}


def candidate_counts(values: Sequence[object]) -> dict[object, int]:
    return dict(Counter(values))


# --- bisect on a sorted list ---------------------------------------------


def baseline_in_range(ordered: Sequence[Probe], lo: Probe, hi: Probe) -> int:
    return sum(1 for value in ordered if lo <= value and value < hi)


def candidate_in_range(ordered: Sequence[Probe], lo: Probe, hi: Probe) -> int:
    # PERF/SAFETY: `ordered` must be sorted ascending by the same ordering.
    return bisect_left(ordered, hi) - bisect_left(ordered, lo)


def candidate_in_closed_range(
    ordered: Sequence[Probe], lo: Probe, hi: Probe
) -> int:
    return bisect_right(ordered, hi) - bisect_left(ordered, lo)


# --- heapq.nsmallest for top-k -------------------------------------------


def baseline_top_k(values: Iterable[Probe], k: int) -> list[Probe]:
    return sorted(values)[:k]


def candidate_top_k(values: Iterable[Probe], k: int) -> list[Probe]:
    return heapq.nsmallest(k, values)


# --- heapq.merge for already-sorted streams -----------------------------


def baseline_merged_total(a: Iterable[int], b: Iterable[int]) -> int:
    total = 0
    for value in sorted([*a, *b]):
        total = total * 31 + value & 0xFFFFFFFF
    return total


def candidate_merged_total(a: Iterable[int], b: Iterable[int]) -> int:
    total = 0
    for value in heapq.merge(a, b):  # inputs must each be sorted
        total = total * 31 + value & 0xFFFFFFFF
    return total


# --- __slots__ -------------------------------------------------------------


class DictPoint:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class SlotPoint:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def baseline_points(n: int) -> int:
    points = [DictPoint(i, -i) for i in range(n)]
    return sum(p.x - p.y for p in points)


def candidate_points(n: int) -> int:
    points = [SlotPoint(i, -i) for i in range(n)]
    return sum(p.x - p.y for p in points)


# --- dataclass(slots=True) ---------------------------------------------


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float


@dataclass(frozen=True, slots=True)
class SlotQuote:
    symbol: str
    price: float


def baseline_quotes(n: int) -> float:
    quotes = [Quote("ABC", i * 0.5) for i in range(n)]
    return sum(q.price for q in quotes)


def candidate_quotes(n: int) -> float:
    quotes = [SlotQuote("ABC", i * 0.5) for i in range(n)]
    return sum(q.price for q in quotes)


# --- array.array for homogeneous numbers --------------------------------


def baseline_samples(n: int) -> float:
    samples = [i * 0.25 for i in range(n)]
    return max(samples, default=0.0)


def candidate_samples(n: int) -> float:
    samples = array("d", (i * 0.25 for i in range(n)))
    return max(samples, default=0.0)


# --- memoryview slices instead of bytes slices --------------------------

HEADER = struct.Struct("<4sI")


def baseline_payload_sum(frame: bytes) -> int:
    _magic, length = HEADER.unpack_from(frame)
    payload = frame[HEADER.size : HEADER.size + length]  # copies
    return sum(payload[::4096])


def candidate_payload_sum(frame: bytes) -> int:
    _magic, length = HEADER.unpack_from(frame)
    with memoryview(frame) as view:
        payload = view[HEADER.size : HEADER.size + length]  # no copy
        return sum(payload[::4096])


# --- bytearray accumulation instead of bytes += -------------------------


def baseline_pack(chunks: Iterable[bytes]) -> bytes:
    out = b""
    for chunk in chunks:
        out += chunk
    return out


def candidate_pack(chunks: Iterable[bytes]) -> bytes:
    out = bytearray()
    for chunk in chunks:
        out += chunk
    return bytes(out)


# --- struct.Struct.iter_unpack instead of per-record unpack -------------

RECORD = struct.Struct("<iHf")


def baseline_records(data: bytes) -> list[tuple[int, int, float]]:
    out: list[tuple[int, int, float]] = []
    for offset in range(0, len(data), 10):
        out.append(struct.unpack("<iHf", data[offset : offset + 10]))
    return out


def candidate_records(data: bytes) -> list[tuple[int, int, float]]:
    # RECORD.size == 10; iter_unpack raises struct.error on a partial tail,
    # like the baseline's unpack of a short slice.
    return list(RECORD.iter_unpack(data))


# --- Oracle --------------------------------------------------------------


def run() -> None:
    allowed = [Probe(i) for i in range(2_000)]
    queries = [Probe(i) for i in (-1, 0, 1_999, 5_000)] * 25
    check.equal(
        "set-membership",
        baseline_known(allowed, queries),
        candidate_known(allowed, queries),
    )
    check.fewer(
        "set-membership",
        "__eq__ calls",
        check.comparisons(lambda: baseline_known(allowed, queries)),
        check.comparisons(lambda: candidate_known(allowed, queries)),
    )

    values = list(range(60_000))
    check.equal("deque", baseline_drain(values), candidate_drain(values))
    check.equal("deque/empty", baseline_drain([]), candidate_drain([]))
    check.at_least_times_faster(
        "deque",
        5,
        lambda: baseline_drain(values),
        lambda: candidate_drain(values),
    )

    words = [Probe(i % 40) for i in range(2_000)]

    def plain(d: dict[object, int]) -> list[tuple[object, int]]:
        return [(k.value, v) for k, v in d.items() if isinstance(k, Probe)]

    check.equal(
        "counter",
        plain(baseline_counts(words)),
        plain(candidate_counts(words)),
    )
    check.fewer(
        "counter",
        "__eq__ calls",
        check.comparisons(lambda: baseline_counts(words)),
        check.comparisons(lambda: candidate_counts(words)),
    )

    ordered = [Probe(i // 3) for i in range(9_000)]
    for lo, hi in ((0, 0), (-5, 2), (100, 200), (2_999, 5_000)):
        a, b = Probe(lo), Probe(hi)
        check.equal(
            "bisect",
            baseline_in_range(ordered, a, b),
            candidate_in_range(ordered, a, b),
        )
    lo, hi = Probe(100), Probe(200)
    check.equal(
        "bisect/closed",
        sum(1 for v in ordered if 100 <= v.value <= 200),
        candidate_in_closed_range(ordered, lo, hi),
    )
    check.fewer(
        "bisect",
        "comparison calls",
        check.comparisons(lambda: baseline_in_range(ordered, lo, hi)),
        check.comparisons(lambda: candidate_in_range(ordered, lo, hi)),
    )

    shuffled = [Probe((i * 7_919) % 10_007) for i in range(10_007)]
    for k in (0, 1, 10, 20_000):
        check.equal(
            "nsmallest",
            [p.value for p in baseline_top_k(shuffled, k)],
            [p.value for p in candidate_top_k(shuffled, k)],
        )
    check.fewer(
        "nsmallest",
        "__lt__ calls",
        check.comparisons(lambda: baseline_top_k(shuffled, 10)),
        check.comparisons(lambda: candidate_top_k(shuffled, 10)),
    )

    evens, odds = range(0, 400_000, 2), range(1, 400_000, 2)
    check.equal(
        "heapq-merge",
        baseline_merged_total(evens, odds),
        candidate_merged_total(evens, odds),
    )
    check.equal(
        "heapq-merge/order",
        sorted([*evens[:50], *odds[:50]]),
        list(heapq.merge(evens[:50], odds[:50])),
    )
    check.fewer(
        "heapq-merge",
        "tracemalloc peak B",
        check.peak_bytes(lambda: baseline_merged_total(evens, odds)),
        check.peak_bytes(lambda: candidate_merged_total(evens, odds)),
    )

    check.equal("slots", baseline_points(10_000), candidate_points(10_000))
    check.fewer(
        "slots",
        "tracemalloc peak B",
        check.peak_bytes(lambda: baseline_points(10_000)),
        check.peak_bytes(lambda: candidate_points(10_000)),
    )

    check.equal(
        "dataclass-slots", baseline_quotes(10_000), candidate_quotes(10_000)
    )
    check.fewer(
        "dataclass-slots",
        "tracemalloc peak B",
        check.peak_bytes(lambda: baseline_quotes(10_000)),
        check.peak_bytes(lambda: candidate_quotes(10_000)),
    )

    for n in (0, 1, 100_000):
        check.equal("array", baseline_samples(n), candidate_samples(n))
    check.fewer(
        "array",
        "tracemalloc peak B",
        check.peak_bytes(lambda: baseline_samples(100_000)),
        check.peak_bytes(lambda: candidate_samples(100_000)),
    )

    body = bytes(range(256)) * 4_096
    frame = HEADER.pack(b"DATA", len(body)) + body
    check.equal(
        "memoryview",
        baseline_payload_sum(frame),
        candidate_payload_sum(frame),
    )
    check.fewer(
        "memoryview",
        "tracemalloc peak B",
        check.peak_bytes(lambda: baseline_payload_sum(frame)),
        check.peak_bytes(lambda: candidate_payload_sum(frame)),
    )

    chunks = [b"\x00\x01\x02\x03" * 8] * 20_000
    check.equal("bytearray", baseline_pack(chunks), candidate_pack(chunks))
    check.equal("bytearray/empty", baseline_pack([]), candidate_pack([]))
    check.at_least_times_faster(
        "bytearray",
        10,
        lambda: baseline_pack(chunks),
        lambda: candidate_pack(chunks),
    )

    data = b"".join(RECORD.pack(i, i % 65_536, i / 4) for i in range(5_000))
    check.equal("struct", baseline_records(data), candidate_records(data))
    check.equal("struct/empty", baseline_records(b""), candidate_records(b""))
    check.fewer(
        "struct",
        "executed instructions",
        check.executed_ops(lambda: baseline_records(data), ("",)),
        check.executed_ops(lambda: candidate_records(data), ("",)),
    )
