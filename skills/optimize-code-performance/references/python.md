# Python performance gotchas

Applies to CPython. Benchmark with `pyperf`, find the hot function with
`python -m cProfile -o out.prof` and `pstats` (or `py-spy` on a running process), memory with
`tracemalloc`, and import time with `python -X importtime -c 'import app'`. Record `python -VV` and
the build: interpreter version changes the answer more than source rewrites do.

## Contents

- [Measurement](#measurement)
- [Algorithms and data structures](#algorithms-and-data-structures)
- [Memory](#memory)
- [Startup](#startup)
- [Concurrency](#concurrency)

## Measurement

- Mistake: `time.time()` around one run, or `timeit` with default repeats. Fix: `pyperf timeit` or a
  `pyperf.Runner` script, which uses several worker processes, a warmup, and reports mean with
  standard deviation; compare runs with `python -m pyperf compare_to old.json new.json`. Run on an
  idle machine; `pyperf system tune` (Linux) reduces noise.
- Mistake: profiling with `cProfile` and trusting the overhead-inflated numbers for small functions.
  Fix: deterministic profiling inflates call-heavy code; confirm with a sampling profiler (`py-spy`,
  `--native` for C extensions) before rewriting.
- Mistake: benchmarking in a REPL or with assertions in debug runs. Fix: run the real script;
  `python -O` only if production does.
- Mistake: measuring `tracemalloc` overhead as a performance change. Fix: `tracemalloc` slows
  allocation; use it to find sites (`take_snapshot().statistics('lineno')`) and time with it off.
- Mistake: input construction included in the measured statement. Fix: pass `setup=` (or build
  inputs before the loop) so only the operation is timed, and give it inputs of production size.

## Algorithms and data structures

- Mistake: membership tests with `x in a_list` in a loop. Fix: build a `set` or `dict` once (keys
  must be hashable and `O(1)` assumes a good `__hash__`).
- Mistake: `list.insert(0, x)` or `pop(0)` for queues. Fix: `collections.deque`; indexing into the
  middle of a deque is O(n).
- Mistake: `s += part` over many parts. Fix: `''.join(parts)`; CPython optimizes some in-place
  string concatenation but the optimization is an implementation detail and absent on other
  interpreters.
- Mistake: sorting with a `cmp_to_key` function. Fix: `key=` with a cheap key (sort is stable, so
  order of equal keys is preserved); `heapq.nsmallest` or `nlargest` when you need only the top few.
- Mistake: materializing a generator into a list to loop once. Fix: keep it lazy, but if the input
  is a generator from a DB cursor, do not hold the whole result; a generator can be consumed only
  once, so a second pass yields nothing.
- Mistake: repeated attribute and global lookups in a hot loop. Fix: bind to locals
  (`append = out.append`) only in the measured hot loop; on 3.11+ the specializing interpreter
  already speeds attribute access, so check the gain.
- Mistake: comprehension replaced by `map`/`filter` with `lambda`. Fix: a comprehension is usually
  faster than `map` with a Python lambda; `map` wins only with a builtin or C function.
- Mistake: rewriting into "clever" one-liners. Fix: keep the code readable; profile-driven changes
  in the hot function only.
- Mistake: `functools.lru_cache` on methods or with unbounded `maxsize`. Fix: a cache on a method
  keeps `self` alive (memory leak) and keys include `self`; bound `maxsize`, and cache only pure
  functions with hashable arguments. `functools.cached_property` needs an instance `__dict__`, so it
  fails with `__slots__` unless `__dict__` is a slot.

## Memory

- Mistake: one Python object per record for millions of records. Fix: `__slots__` (or
  `@dataclass(slots=True)` on 3.10+) removes the per-instance `__dict__`; tuples, `array.array`,
  NumPy arrays, or columnar storage reduce it further. Check inheritance: a subclass without
  `__slots__` gets a `__dict__` again, and slots break pickled compatibility and `weakref` unless
  `__weakref__` is listed.
- Mistake: `sys.getsizeof` as total memory. Fix: it reports the shallow size only; measure with
  `tracemalloc` or process RSS.
- Mistake: reading a whole file into a list. Fix: iterate lines from the file object, or use `mmap`
  or chunks; `json.load` of a huge document still builds it all, so use a streaming parser when that
  is the cost.
- Mistake: expecting freed memory to shrink RSS. Fix: CPython's allocator keeps arenas; peak RSS can
  stay high after objects are freed. Process large batches in a worker process that exits.
- Mistake: disabling the garbage collector (`gc.disable()`) for speed. Fix: it leaks reference
  cycles. `gc.freeze()` after startup in pre-fork servers, or raising thresholds, are narrower
  options; measure with `gc.get_stats()`.

## Startup

- Mistake: optimizing CPU code when `python -m app --help` is slow. Fix: run `python -X importtime`
  and defer the heavy imports to the function that needs them (import inside the function or
  `importlib.util.LazyLoader`). A deferred import moves the failure to call time, and import side
  effects (registries, plugins) then run later, so check who relies on them.

## Concurrency

- Mistake: `multiprocessing.Pool` for I/O-bound waits. Fix: threads or `asyncio` (`asyncio.gather`
  with a semaphore); processes add pickling and start-up cost and suit CPU-bound work. Arguments and
  results must be picklable; workers do not share module state.
- Mistake: threads for CPU-bound pure Python. Fix: the GIL serializes bytecode on the default build,
  so use processes, or vectorize with NumPy. Free-threaded builds (PEP 703, `python3.13t` and later)
  remove the GIL, but single-thread speed and extension compatibility differ; measure on that exact
  build before switching a deployment.
- Mistake: `asyncio` with blocking calls (`requests`, `time.sleep`, file I/O, CPU loops). Fix: use
  async libraries, or `asyncio.to_thread` or `run_in_executor`; one blocking call stalls every task
  on the loop. `create_task` without a kept reference can be garbage collected.
- Mistake: creating a `ProcessPoolExecutor` per call, or forking after threads start. Fix: one pool
  per application; on Linux prefer `spawn` or `forkserver` when threads exist (`fork` copies a
  locked state), and mind that 3.14 changes the default start method on Linux to `forkserver`.
- Mistake: enabling the experimental JIT (3.13+) or switching builds by Dockerfile for speed without
  measurement. Fix: it is off by default, its gains depend on the workload and build, and it may be
  absent from the distribution's interpreter. Benchmark the exact image.
- Mistake: rewriting hot code in Cython, Rust, or C first. Fix: confirm with the profile that a
  vectorized library call (NumPy, `itertools`, builtins such as `sum`, `sorted`, `str.join`) cannot
  do it; native extensions add build and packaging cost and cross-boundary conversion overhead per
  call, so batch the crossings.
