# Concurrency constructs

Pick a concurrency model by what dominates wall time. Waiting (network, disk,
subprocess, sleep) overlaps with threads or asyncio. Pure-Python CPU work
needs several processes or interpreters on a GIL build, or a free-threaded
build. Examples are in
[`concurrency.py`](../assets/examples/constructs/concurrency.py) and
[`interp_worker.py`](../assets/examples/constructs/interp_worker.py).

Tier: Executed (`sh assets/examples/verify.sh verify`), except the
free-threaded speedup, which is not runnable here. Local results are
machine-specific: Apple M1 Max (10 cores), macOS, Homebrew CPython 3.14.7,
GIL build, default start method `spawn`. Wall-clock assertions use a lower
bound that holds by construction: 10 calls that each sleep 50 ms take at
least 0.5 s in sequence, and the candidate must finish in under half that.

## Contents

- ProcessPoolExecutor for CPU-bound work
- ThreadPoolExecutor for blocking I/O
- asyncio.TaskGroup for concurrent awaits
- asyncio.to_thread for blocking calls in async code
- InterpreterPoolExecutor
- Threads on a free-threaded build

## ProcessPoolExecutor for CPU-bound work

**Definition.** `ProcessPoolExecutor(max_workers)` runs callables in worker
processes, each with its own interpreter and GIL. Arguments and results are
pickled. `map(fn, it, chunksize=n)` sends batches, which only
`ProcessPoolExecutor` supports. The default `max_workers` is
`os.process_cpu_count()`. On Windows it is capped at 61
([concurrent.futures][futures]).

**Use when.**

- A profile shows pure-Python CPU work that splits into independent tasks
  (parsing files, simulations, per-item transforms).
- Each task's compute time is much larger than the cost of pickling its
  inputs and outputs.

**Do not use when.**

- The tasks are tiny: process start-up (spawn on macOS and Windows) and
  pickling dominate. Measured: a 300,000-iteration batch got slower in the
  pool (0.140 s -> 0.166 s); a 2,000,000-iteration batch got faster (0.96 s
  -> 0.36 s). Raise `chunksize` or batch the work.
- The callable is a lambda, a closure, or defined in `__main__` of an
  interactive session: it cannot be pickled, or workers cannot import it.
  Workers must be able to import the `__main__` module.
- The code relies on `fork` inheriting state. Since 3.14 the default start
  method on POSIX is `forkserver` (macOS uses `spawn`); request `fork`
  explicitly with `get_context("fork")`
  ([What's New 3.14][wn314-mp]).
- The work is I/O-bound: threads or asyncio overlap waits without pickling.

**Example.**

```python
def cpu_task(n: int) -> tuple[int, int]:  # module level: importable
    total = 0
    for i in range(n):
        total += i * i % 7
    return total, os.getpid()

def candidate_cpu(sizes, workers=4):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return [t for t, _ in pool.map(cpu_task, sizes, chunksize=1)]
```

Guard the entry point with `if __name__ == "__main__":`; under `spawn`, each
worker imports the main module.

**Cost removed.** Serial CPU time. Measured, 8 tasks × 2,000,000 iterations,
4 workers: 0.96 s -> 0.36 s wall (reported, not asserted). The deterministic
check is that 4 distinct worker PIDs ran tasks.

**Verify.**

1. `sh assets/examples/verify.sh verify` checks equal results and
   `METRIC process-pool distinct worker pids: 1 -> 4`.
1. Time the application-level command, pool start-up included, with
   `hyperfine` or pyperf `bench_func`. Keep the change only if total wall
   time drops.

## ThreadPoolExecutor for blocking I/O

**Definition.** `ThreadPoolExecutor(max_workers)` runs callables in threads
of one process. Blocking I/O releases the GIL while waiting, so waits
overlap. `map` returns results in input order. The default `max_workers` is
`min(32, (os.process_cpu_count() or 1) + 4)` on 3.13+
([concurrent.futures][futures]).

**Use when.**

- A profile or trace shows wall time dominated by independent blocking
  calls (HTTP client, database driver, file reads, `subprocess.run`).
- The client library is synchronous and thread-safe.

**Do not use when.**

- The work is pure-Python CPU on a GIL build: threads take turns on one core
  and add switching cost.
- The client object is not thread-safe (some database connections): give
  each thread its own client, or use a pool.
- The remote side enforces rate limits and `max_workers` is unbounded:
  fan-out causes throttling or errors.

**Example.**

```python
def candidate_fetch_all(keys):
    with ThreadPoolExecutor(max_workers=len(keys) or 1) as pool:
        return list(pool.map(blocking_fetch, keys))  # input order
```

**Cost removed.** Serialized waiting. Measured, 10 × 50 ms blocking calls:
0.056 s in the pool against a 0.5 s serial lower bound.

**Verify.**

1. `verify.sh verify` checks equal, ordered results.
1. The same run asserts candidate wall < 0.25 s (half the serial lower
   bound). In the project, measure the request's end-to-end latency.

## asyncio.TaskGroup for concurrent awaits

**Definition.** `async with asyncio.TaskGroup() as tg:` (3.11+) starts tasks
with `tg.create_task()` and waits for all of them on exit. If one task fails
with anything other than `CancelledError`, the group cancels the rest and
raises an `ExceptionGroup` ([asyncio tasks][asyncio-tg]).

**Use when.**

- Code awaits independent, waiting-bound coroutines one after another
  (`[await f(k) for k in keys]`).
- The libraries involved are asyncio-native (aiohttp, asyncpg, asyncio
  streams).

**Do not use when.**

- The coroutines call blocking functions: they block the event loop, and
  nothing overlaps (see the to_thread card).
- Callers catch a specific exception type: TaskGroup raises
  `ExceptionGroup`, so `except ValueError` no longer matches. Switch callers
  to `except* ValueError`, or keep `asyncio.gather` for its first-error
  semantics: with `gather`, the other awaitables keep running.
- The fan-out has no bound and the remote side limits rates: add an
  `asyncio.Semaphore`.

**Example.**

```python
async def candidate_gather(keys):
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(async_fetch(k)) for k in keys]
    return [task.result() for task in tasks]  # input order
```

**Cost removed.** Serialized awaits. Measured, 10 × `asyncio.sleep(0.05)`:
0.051 s wall against a 0.5 s serial lower bound.

**Verify.**

1. `verify.sh verify` checks equal, ordered results.
1. The same run asserts candidate wall < 0.25 s. Also test the failure
   path: one failing task cancels the others and surfaces in an
   `ExceptionGroup`.

## asyncio.to_thread for blocking calls in async code

**Definition.** `await asyncio.to_thread(func, *args)` (3.9+) runs a blocking
function in the loop's default thread pool without blocking the event loop.
Because of the GIL, it "can typically only be used to make IO-bound functions
non-blocking"
([asyncio.to_thread][asyncio-to-thread]).

**Use when.**

- An `async def` calls a synchronous blocking API (file I/O, a sync SDK,
  `time.sleep`, DNS) that has no async version.
- Event-loop lag or asyncio debug-mode warnings about slow callbacks point
  at that call.

**Do not use when.**

- The function is CPU-bound Python on a GIL build: it still competes with the
  event loop for the GIL. Use a process pool through
  `loop.run_in_executor`.
- The function uses thread-affine state (thread-locals, some GUI or database
  handles).

**Example.**

```python
async def candidate_blocking_in_loop(keys):
    calls = (asyncio.to_thread(blocking_fetch, k) for k in keys)
    return list(await asyncio.gather(*calls))
```

**Cost removed.** Event-loop blocking. Measured, 10 × 50 ms blocking calls:
the candidate took 0.056 s; the baseline blocks the loop, so it takes at
least 0.5 s by construction.

**Verify.**

1. `verify.sh verify` checks equal results.
1. The same run asserts candidate wall < 0.25 s. In the project, run with
   `PYTHONASYNCIODEBUG=1`; the "Executing ... took" warnings for that call
   must disappear.

## InterpreterPoolExecutor

**Definition.** `concurrent.futures.InterpreterPoolExecutor` (3.14+) is a
`ThreadPoolExecutor` subclass. Each worker thread runs its own isolated
interpreter with its own GIL, so pure-Python CPU work runs in parallel in one
process. The callable, its arguments, and its results are pickled between
interpreters ([concurrent.futures][futures-interp],
[What's New 3.14][wn314-interp]).

**Use when.**

- The project requires Python 3.14+, the work is pure-Python CPU, and
  process start-up or memory per process is the problem with
  `ProcessPoolExecutor`.
- Every module that the worker imports supports subinterpreters.

**Do not use when.**

- The worker's import graph includes a module that does not support
  subinterpreters. Measured: importing `tracemalloc` in a subinterpreter
  raised `ImportError: module _tracemalloc does not support loading in
  subinterpreters`, surfaced as `NotShareableError`, although What's New
  says all stdlib extension modules are compatible. Keep the worker in a
  module with minimal imports (`interp_worker.py`).
- Third-party C extensions are involved: many are not yet compatible
  ([What's New 3.14][wn314-interp]).
- Tasks share mutable state: interpreters are isolated, and only immutable
  shareable objects and `memoryview` data cross between them.
- The project supports 3.13 or earlier: the class does not exist there.

**Example.**

```python
# interp_worker.py imports only sys and concurrent.interpreters
from concurrent.futures import InterpreterPoolExecutor
from interp_worker import interpreter_task

with InterpreterPoolExecutor(max_workers=4) as pool:
    rows = list(pool.map(interpreter_task, sizes))
```

**Cost removed.** Serial CPU time, without separate processes. Measured: 4
distinct interpreter IDs ran the 8 tasks, with results equal to the serial
baseline.

**Verify.**

1. `verify.sh verify` checks equal results and `METRIC interpreter-pool
   distinct interpreters: 1 -> 4`. On Python below 3.14 it prints `SKIP`.
1. Time the application-level command before and after, pool start-up
   included, with pyperf or `hyperfine`.

## Threads on a free-threaded build

**Definition.** Free-threaded CPython (PEP 703; `python3.13t`,
`python3.14t`) runs without the GIL, so Python threads run CPU work in
parallel. `sysconfig.get_config_var("Py_GIL_DISABLED") == 1` identifies the
build. `sys._is_gil_enabled()` (3.13+) reports whether the GIL is actually
off at runtime. The GIL can come back through `PYTHON_GIL=1`, `-X gil=1`,
or importing a C extension that is not marked free-threading-safe, which
prints a warning ([free-threading HOWTO][ft-howto], [sys][sys-gil]).

**Use when.**

- The deployment uses or can adopt a `t` build, and CPU-bound work splits
  into threads with no shared mutable state (or with explicit locks).
- `sys._is_gil_enabled()` returns `False` in the deployed process, not only
  on the build machine.

**Do not use when.**

- An extension re-enables the GIL at import: threads serialize again. Check
  `sys._is_gil_enabled()` after all imports.
- Correctness relies on the GIL making compound operations atomic. Built-in
  containers lock internally, but the docs call this "a description of the
  current implementation, not a guarantee". Use `threading.Lock`.
- Threads share one iterator: "threads may see duplicate or missing
  elements" ([free-threading HOWTO][ft-howto]).
- Single-thread speed matters most. For 3.14 the sources disagree on the
  overhead: the HOWTO gives about 1% (macOS aarch64) to 8% (x86-64 Linux) on
  pyperformance ([free-threading HOWTO][ft-howto]), and What's New 3.14
  says "roughly 5-10%" ([What's New 3.14][wn314-ft]). Measure your
  workload on both builds.
- The version is 3.13: free-threading was experimental there, with "a
  substantial single-threaded performance hit" ([What's New 3.13][wn313-ft]).
  PEP 779 made it officially supported in 3.14.

**Example.**

```python
import sys, sysconfig

def gil_enabled() -> bool:
    if sys.version_info >= (3, 13):
        return sys._is_gil_enabled()
    return True

build = sysconfig.get_config_var("Py_GIL_DISABLED") == 1
if build and not gil_enabled():
    results = threaded_cpu(sizes)  # disjoint writes, no shared iterator
```

**Cost removed.** Serial CPU time in threads. Not measured here.

**Verify.** Tier: detection executed; the parallel path is not runnable here
(no `python3.14t` on this machine).

1. `verify.sh verify` checks that `threaded_cpu` equals the serial result and
   prints `SKIP free-threading speedup: GIL enabled`.
1. On a `t` build, the same command asserts threaded wall time below serial
   wall time. `python3.14t -VV` must print "free-threading build".

[asyncio-tg]: https://docs.python.org/3/library/asyncio-task.html#task-groups
[asyncio-to-thread]:
  https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
[ft-howto]: https://docs.python.org/3/howto/free-threading-python.html
[futures]: https://docs.python.org/3/library/concurrent.futures.html
[futures-interp]:
  https://docs.python.org/3/library/concurrent.futures.html#interpreterpoolexecutor
[sys-gil]: https://docs.python.org/3/library/sys.html#sys._is_gil_enabled
[wn313-ft]:
  https://docs.python.org/3/whatsnew/3.13.html#free-threaded-cpython
[wn314-ft]: https://docs.python.org/3/whatsnew/3.14.html#whatsnew314-free-threaded-now-supported
[wn314-interp]:
  https://docs.python.org/3/whatsnew/3.14.html#whatsnew314-multiple-interpreters
[wn314-mp]: https://docs.python.org/3/whatsnew/3.14.html#multiprocessing
