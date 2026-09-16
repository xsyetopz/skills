"""The mutant and correction face the same observable contract. Python 3.10+."""

from __future__ import annotations
import asyncio
import math
import sys


async def cancelled_contract(bad: bool) -> bool:
    ready = asyncio.Event()

    async def worker() -> None:
        ready.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if not bad:
                raise

    task = asyncio.create_task(worker())
    await (
        ready.wait()
    )  # Establish that the worker entered the cancellable region.
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return True
    return False


def contract(bad: bool, topic: int) -> bool:
    if topic == 1:
        shared: list[int] = []

        def add(value: int, output: list[int] | None = None) -> list[int]:
            target = (shared if bad else []) if output is None else output
            target.append(value)
            return target

        first, second = add(1), add(2)
        return first == [1] and second == [2] and first is not second
    if topic == 2:
        source = iter([1, 2, 3])
        result = source if bad else list(source)
        first, second = list(result), list(result)
        return first == second == [1, 2, 3]
    if topic == 3:
        values = ["first", "first", "second"]
        result = list(set(values)) if bad else list(values)
        return result == ["first", "first", "second"]
    if topic == 4:
        items = [(2, "first"), (2, "second")]
        result = (
            sorted(items, reverse=True)[0]
            if bad
            else max(items, key=lambda item: item[0])
        )
        return result == (2, "first")
    if topic == 5:
        values = [1e16, 1.0, -1e16]
        result = sum(values) if bad else math.fsum(values)
        # Builtin sum gained compensated summation in Python 3.12: explicitly
        # model the unsafe regrouping instead of assuming sum is always naive.
        if bad:
            result = (values[0] + values[1]) + values[2]
        return result == 1.0
    if topic == 6:
        caught = BaseException if bad else ValueError

        def work() -> None:
            try:
                raise KeyboardInterrupt()
            except caught:
                pass

        try:
            work()
        except KeyboardInterrupt:
            return True
        return False
    if topic == 7:
        return asyncio.run(cancelled_contract(bad))
    if topic == 8:
        rows = [[0]] * 2 if bad else [[0] for _ in range(2)]
        rows[0][0] = 1
        return rows[1][0] == 0
    raise ValueError("topic must be 1..8")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"red", "green"}:
        raise SystemExit("usage: red|green TOPIC")
    topic = int(sys.argv[2])
    passed = contract(sys.argv[1] == "red", topic)
    print(f"CONTRACT topic {topic}: {'PASS' if passed else 'FAIL'}")
    raise SystemExit(0 if passed else 1)
