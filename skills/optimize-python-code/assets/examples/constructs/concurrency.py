"""Concurrency constructs: processes and interpreters for CPU work, threads
and asyncio for waiting. See references/concurrency.md.

Worker functions live at module level so ProcessPoolExecutor (spawn on
macOS and Windows) and InterpreterPoolExecutor can import them by name.
"""

import asyncio
import os
import sys
import sysconfig
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import check
from interp_worker import interpreter_task

# --- CPU-bound work: processes -------------------------------------------


def cpu_task(n: int) -> tuple[int, int]:
    total = 0
    for i in range(n):
        total += i * i % 7
    return total, os.getpid()


def baseline_cpu(sizes: Sequence[int]) -> list[int]:
    return [cpu_task(n)[0] for n in sizes]


def candidate_cpu(sizes: Sequence[int], workers: int = 4) -> list[int]:
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return [total for total, _ in pool.map(cpu_task, sizes, chunksize=1)]


def worker_pids(sizes: Sequence[int], workers: int = 4) -> set[int]:
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return {pid for _, pid in pool.map(cpu_task, sizes, chunksize=1)}


# --- Blocking I/O: threads -----------------------------------------------


def blocking_fetch(key: int, delay: float = 0.05) -> str:
    time.sleep(delay)  # stands in for a socket/file call that releases the GIL
    return f"payload-{key}"


def baseline_fetch_all(keys: Sequence[int]) -> list[str]:
    return [blocking_fetch(key) for key in keys]


def candidate_fetch_all(keys: Sequence[int]) -> list[str]:
    with ThreadPoolExecutor(max_workers=len(keys) or 1) as pool:
        return list(pool.map(blocking_fetch, keys))  # keeps input order


# --- Non-blocking I/O: asyncio.TaskGroup --------------------------------


async def async_fetch(key: int, delay: float = 0.05) -> str:
    await asyncio.sleep(delay)
    return f"payload-{key}"


async def baseline_gather(keys: Sequence[int]) -> list[str]:
    return [await async_fetch(key) for key in keys]


async def candidate_gather(keys: Sequence[int]) -> list[str]:
    if sys.version_info < (3, 11):
        return list(await asyncio.gather(*(async_fetch(k) for k in keys)))
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(async_fetch(key)) for key in keys]
    return [task.result() for task in tasks]


# --- Blocking call inside async code: asyncio.to_thread -----------------


async def baseline_blocking_in_loop(keys: Sequence[int]) -> list[str]:
    async def one(key: int) -> str:
        return blocking_fetch(key)  # blocks the event loop

    return list(await asyncio.gather(*(one(key) for key in keys)))


async def candidate_blocking_in_loop(keys: Sequence[int]) -> list[str]:
    calls = (asyncio.to_thread(blocking_fetch, key) for key in keys)
    return list(await asyncio.gather(*calls))


# --- Subinterpreters (3.14+) ---------------------------------------------


def candidate_interpreters(sizes: Sequence[int]) -> tuple[list[int], set[int]]:
    if sys.version_info < (3, 14):
        raise RuntimeError("InterpreterPoolExecutor requires Python 3.14+")
    from concurrent.futures import InterpreterPoolExecutor

    with InterpreterPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(interpreter_task, sizes))
    return [total for total, _ in rows], {ident for _, ident in rows}


# --- Free-threaded build (3.13t/3.14t) -----------------------------------


def gil_enabled() -> bool:
    if sys.version_info >= (3, 13):
        return sys._is_gil_enabled()
    return True


def threaded_cpu(sizes: Sequence[int]) -> list[int]:
    results = [0] * len(sizes)

    def work(index: int) -> None:
        results[index] = cpu_task(sizes[index])[0]  # disjoint slots

    threads = [
        threading.Thread(target=work, args=(i,)) for i in range(len(sizes))
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def wall(action: Callable[[], object]) -> float:
    start = time.perf_counter()
    action()
    return time.perf_counter() - start


def run() -> None:
    sizes = [2_000_000] * 8
    expected = baseline_cpu(sizes)
    check.equal("process-pool", expected, candidate_cpu(sizes))
    pids = worker_pids(sizes)
    check.more("process-pool", "distinct worker pids", 1, len(pids))
    seq = wall(lambda: baseline_cpu(sizes))
    par = wall(lambda: candidate_cpu(sizes))
    print(f"METRIC process-pool wall s (report only): {seq:.3f} -> {par:.3f}")

    keys = list(range(10))
    check.equal(
        "thread-pool", baseline_fetch_all(keys), candidate_fetch_all(keys)
    )
    serial = 10 * 0.05  # lower bound of the baseline by construction
    check.fewer(
        "thread-pool",
        "wall s vs half the serial lower bound",
        serial / 2,
        wall(lambda: candidate_fetch_all(keys)),
    )

    check.equal(
        "taskgroup",
        asyncio.run(baseline_gather(keys)),
        asyncio.run(candidate_gather(keys)),
    )
    check.fewer(
        "taskgroup",
        "wall s vs half the serial lower bound",
        serial / 2,
        wall(lambda: asyncio.run(candidate_gather(keys))),
    )

    check.equal(
        "to-thread",
        asyncio.run(baseline_blocking_in_loop(keys)),
        asyncio.run(candidate_blocking_in_loop(keys)),
    )
    check.fewer(
        "to-thread",
        "wall s vs half the serial lower bound",
        serial / 2,
        wall(lambda: asyncio.run(candidate_blocking_in_loop(keys))),
    )

    if sys.version_info >= (3, 14):
        totals, idents = candidate_interpreters(sizes)
        check.equal("interpreter-pool", expected, totals)
        check.more(
            "interpreter-pool",
            "distinct interpreters",
            1,
            len(idents),
        )
    else:
        print("SKIP interpreter-pool: requires Python 3.14+")

    build = sysconfig.get_config_var("Py_GIL_DISABLED") == 1
    check.equal("free-threading/result", expected, threaded_cpu(sizes))
    if build and not gil_enabled():
        seq = wall(lambda: baseline_cpu(sizes))
        check.fewer(
            "free-threading",
            "wall s",
            seq,
            wall(lambda: threaded_cpu(sizes)),
        )
    else:
        print(
            "SKIP free-threading speedup: GIL enabled "
            f"(Py_GIL_DISABLED={int(build)}); needs python3.13t/3.14t"
        )
