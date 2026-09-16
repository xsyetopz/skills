"""Eight checked baseline/candidate pairs; no speed claims."""

from collections import Counter, deque
from collections.abc import Callable, Sequence
from typing import Any
import argparse
import json


def baseline_queue(values: Sequence[int]) -> list[int]:
    pending = list(values)
    result: list[int] = []
    while pending:
        result.append(pending.pop(0))
    return result


def candidate_queue(values: Sequence[int]) -> list[int]:
    pending = deque(values)
    result: list[int] = []
    while pending:
        result.append(pending.popleft())
    return result


def baseline_join(values: Sequence[str]) -> str:
    result = ""
    # Retain the prior prefix instead of relying on CPython's optional +=
    # shortcut.
    prior = [result]
    for value in values:
        prior[0] = result
        result = result + value
    return result


def candidate_join(values: Sequence[str]) -> str:
    return "".join(values)


def baseline_membership(
    values: Sequence[str], queries: Sequence[str]
) -> list[bool]:
    return [query in values for query in queries]


def candidate_membership(
    values: Sequence[str], queries: Sequence[str]
) -> list[bool]:
    members = set(values)
    return [query in members for query in queries]


def baseline_counts(values: Sequence[str]) -> dict[str, int]:
    return {value: values.count(value) for value in values}


def candidate_counts(values: Sequence[str]) -> dict[str, int]:
    return dict(Counter(values))


def baseline_sum(values: Sequence[int]) -> int:
    return sum([value * value for value in values if value % 2 == 0])


def candidate_sum(values: Sequence[int]) -> int:
    return sum(value * value for value in values if value % 2 == 0)


def baseline_max(values: Sequence[int]) -> int | None:
    return sorted(values)[-1] if values else None


def candidate_max(values: Sequence[int]) -> int | None:
    return max(values, default=None)


def baseline_count_zero(values: bytes) -> int:
    count = 0
    for value in values:
        if value == 0:
            count += 1
    return count


def candidate_count_zero(values: bytes) -> int:
    return values.count(0)


class DictPoint:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class SlottedPoint:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def baseline_dict_points(values: Sequence[int]) -> int:
    points = [DictPoint(value, index) for index, value in enumerate(values)]
    return sum(point.x + point.y for point in points)


def candidate_slotted_points(values: Sequence[int]) -> int:
    points = [SlottedPoint(value, index) for index, value in enumerate(values)]
    return sum(point.x + point.y for point in points)


PAIRS: tuple[tuple[Callable[..., Any], Callable[..., Any]], ...] = (
    (baseline_queue, candidate_queue),
    (baseline_join, candidate_join),
    (baseline_membership, candidate_membership),
    (baseline_counts, candidate_counts),
    (baseline_sum, candidate_sum),
    (baseline_max, candidate_max),
    (baseline_count_zero, candidate_count_zero),
    (baseline_dict_points, candidate_slotted_points),
)


def workload(case: int, size: int) -> tuple[Any, ...]:
    numbers = [(i % 31) - 15 for i in range(size)]
    strings = [str(number) for number in numbers]
    if case == 3:
        return strings, ["missing", "0", "-15"] * max(1, size // 3)
    if case in (2, 4):
        return (strings,)
    if case == 7:
        return (bytes(value & 0xFF for value in numbers),)
    return (numbers,)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=("baseline", "candidate"))
    parser.add_argument("case", type=int, choices=range(1, 9))
    parser.add_argument("size", type=int)
    args = parser.parse_args()
    if not 0 <= args.size <= 100_000:
        parser.error(
            "size must be in [0, 100000]; BASELINE includes quadratic work"
        )
    result = PAIRS[args.case - 1][args.variant == "candidate"](
        *workload(args.case, args.size)
    )
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
