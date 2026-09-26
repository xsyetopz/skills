---
name: optimize-python-code
description: >-
  Profiles and optimizes CPython time and memory with pyperf, cProfile,
  tracemalloc, and import timing. Use when a Python benchmark or profile shows
  the cost. Not for readability-only refactors.
---

# Optimize Python Code

Make a measured CPython hot path cheaper without changing observable
behavior. Each change applies one reference card to a cost that a profile
attributes, is checked by a differential oracle, and is kept only if the
metric the card names improves. The cards record preconditions, version
gates, and traps, so read the card before applying a construct.

## Workflow

1. Record the target. Run `python -VV`, read `requires-python` in
   `pyproject.toml`, and note the lockfile and the deployment interpreter.
   Check whether it is a free-threaded build
   (`sysconfig.get_config_var("Py_GIL_DISABLED")`) and whether a JIT is
   enabled. Keep the project's minimum version; a construct gated to a
   newer Python needs a version guard or an explicit request.
1. Reproduce the workload with representative inputs. Pick the metric the
   user cares about: CPU time, wall latency, throughput, peak traced
   memory, RSS, or start-up time.
1. Attribute the cost before editing. Commands and interpretation are in
   [measurement](references/measurement.md).
   - CPU in Python functions: `python -m cProfile -o out.prof -s cumulative
     app.py`, then `python -m pstats out.prof`.
   - Memory growth: tracemalloc snapshot diff grouped by `lineno`.
   - Start-up: `python -X importtime -c 'import pkg' 2>&1 | tail`.
   - Native or mixed stacks on Linux: `perf record` with `-X perf`.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first. Run baseline and candidate on the same inputs,
   including empty input, a one-shot iterator, duplicates, ties, and error
   cases (see the differential oracle card in
   [measurement](references/measurement.md)). Use the project's test runner.
1. Apply the change. Comment every invariant the card requires (for example,
   "the global is not rebound", "the input is sorted", "the view does not
   outlive the buffer").
1. Verify with the card's **Verify** steps: behavior first, then the named
   metric (calls, executed instructions, comparisons, traced bytes).
1. Time the pair with pyperf in the same interpreter and on the same machine:
   `bench_func` in worker processes, then `python -m pyperf compare_to
   base.json cand.json --table`. Keep the change only if the row is
   significant in the intended direction and nothing else regressed. Then
   re-run the application-level workload.
1. Report using [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| No test proves baseline and candidate equal | [Differential oracle](references/measurement.md#differential-equivalence-oracle) |
| Need a quick in-process timing | [timeit](references/measurement.md#timeit-with-the-minimum-of-repeats) |
| Need a keep/revert timing decision | [bench_func](references/measurement.md#pyperf-runnerbench_func), [pyperf timeit](references/measurement.md#pyperf-timeit-command), [compare_to](references/measurement.md#pyperf-compare_to) |
| Unknown which function costs time | [cProfile](references/measurement.md#cprofile-and-pstats) |
| Memory claim, need a number | [tracemalloc peak](references/measurement.md#tracemalloc-peak-as-an-allocation-oracle) |
| Memory grows, unknown line | [Snapshot diff](references/measurement.md#tracemalloc-snapshot-diff) |
| Need exact call counts without timing overhead | [sys.monitoring](references/measurement.md#sysmonitoring-call-counter) |
| Claim is about loads, calls, or loop iterations | [Instruction counting](references/measurement.md#executed-instruction-counting) |
| Slow start-up or CLI | [-X importtime](references/measurement.md#python--x-importtime), [Deferred import](references/runtime.md#deferred-import) |
| Time hidden in C extensions (Linux) | [perf trampoline](references/measurement.md#linux-perf-trampoline) |
| `math.sqrt`, `len`, and similar globals called in a hot loop | [Local binding](references/interpreter.md#local-binding-of-module-attributes) |
| `out.append(...)` per iteration | [Hoist method](references/interpreter.md#hoisting-a-bound-method), [Comprehension](references/interpreter.md#list-comprehension-instead-of-an-append-loop) |
| Python loop computing count, search, max, or dedupe | [C methods](references/interpreter.md#c-implemented-methods-instead-of-python-loops) |
| `sum([...])`, `max([...])` temporaries | [Generator expression](references/interpreter.md#generator-expression-instead-of-a-temporary-list) |
| `sum(lists, [])` or `acc = acc + row` | [chain.from_iterable](references/interpreter.md#itertoolschainfrom_iterable-instead-of-sumlists-) |
| `s += piece` in a loop | [str.join](references/interpreter.md#strjoin-instead-of-repeated-concatenation), [StringIO](references/interpreter.md#iostringio-for-incremental-writers) |
| `key=lambda r: r[1]` over many rows | [itemgetter](references/interpreter.md#operatoritemgetter-and-attrgetter-keys) |
| `re.match(CONST, s)` per record | [re.compile](references/interpreter.md#precompiled-regular-expressions) |
| Same pure call repeated with same args | [functools.cache](references/interpreter.md#functoolscache-and-lru_cache) |
| `x in list` inside a loop | [set membership](references/containers.md#set-or-dict-membership-instead-of-list-membership) |
| `list.pop(0)` or `insert(0, x)` | [deque](references/containers.md#collectionsdeque-for-fifo-queues) |
| `list.count` per element, manual tallies | [Counter](references/containers.md#collectionscounter-instead-of-listcount-per-element) |
| Range or rank queries on sorted data | [bisect](references/containers.md#bisect-on-a-sorted-list) |
| `sorted(xs)[:k]` with small k | [nsmallest](references/containers.md#heapqnsmallest-and-nlargest-for-top-k) |
| Sorting concatenated sorted inputs | [heapq.merge](references/containers.md#heapqmerge-for-sorted-streams) |
| Many small instances dominate memory | [\_\_slots\_\_](references/containers.md#__slots__), [dataclass slots](references/containers.md#dataclassslotstrue) |
| Large lists of numbers | [array.array](references/containers.md#arrayarray-for-homogeneous-numbers) |
| `data[a:b]` copies of large bytes | [memoryview](references/containers.md#memoryview-slices) |
| `bytes +=` in a loop | [bytearray](references/containers.md#bytearray-accumulation) |
| `struct.unpack` per record with slicing | [struct.Struct](references/containers.md#structstruct-precompiled-formats) |
| Pure-Python CPU work that splits into tasks | [ProcessPoolExecutor](references/concurrency.md#processpoolexecutor-for-cpu-bound-work), [InterpreterPoolExecutor](references/concurrency.md#interpreterpoolexecutor) |
| Wall time dominated by blocking I/O | [ThreadPoolExecutor](references/concurrency.md#threadpoolexecutor-for-blocking-io) |
| Sequential `await` of independent calls | [TaskGroup](references/concurrency.md#asynciotaskgroup-for-concurrent-awaits) |
| Blocking call inside `async def` | [to_thread](references/concurrency.md#asyncioto_thread-for-blocking-calls-in-async-code) |
| CPU threads on 3.13t/3.14t | [Free-threaded build](references/concurrency.md#threads-on-a-free-threaded-build) |
| Micro-optimization measured no gain on 3.11+ | [Specialization](references/runtime.md#specializing-adaptive-interpreter) |
| Asked to "turn on the JIT" | [Experimental JIT](references/runtime.md#experimental-jit) |

## Rules

- The same interpreter binary, flags, environment, inputs, and machine for
  baseline and candidate. pyperf workers receive a reduced environment, so
  pass `--inherit-environ` for variables such as `PYTHON_JIT`.
- One construct per measured change, so each result is attributable.
  Revert a change whose pyperf row is not significant; do not keep
  "harmless" rewrites.
- A candidate that does less work (skipped validation, cached result,
  different input, early exit) is invalid even if it is faster.
- Preserve laziness, iteration count, ordering and tie rules, exception
  types and timing, `None`/falsy distinctions, identity, and float results.
  `sum` uses compensated summation since 3.12, so a manual float loop is not
  equivalent.
- Never widen a public signature (default-argument binding) or weaken
  thread-safety to get speed. Never catch `BaseException` in a fast path.
- Do not quote timings from cProfile, tracemalloc, or `sys.monitoring`
  runs: those tools slow the code they observe.
- Gate version-specific APIs: `sys.monitoring` needs 3.12+,
  `sys._is_gil_enabled` 3.13+, and `InterpreterPoolExecutor` and `sys._jit`
  3.14+. `-X perf` is Linux-only. The JIT is experimental and not for
  production.
- Report only numbers you measured (with machine, OS, and interpreter) or
  numbers from a cited primary source.

## Bundled tools

- `assets/examples/verify.sh verify|benchmark|measure` runs the construct
  catalog in a temporary copy. `verify` (stdlib only) runs every
  equivalence oracle and deterministic benefit check. `benchmark` is a
  pyperf smoke run. `measure` writes pyperf JSON for both variants and
  prints `compare_to --table`. `PYTHON` selects the interpreter.
  `benchmark` and `measure` need pyperf.
- `assets/examples/constructs/check.py` provides oracle helpers to copy into
  a project's tests: `peak_bytes`, `executed_ops`, `python_calls`, `Probe`
  comparison counting, and `at_least_times_faster` for asymptotic gaps.
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): the oracle, timeit, pyperf,
  cProfile, tracemalloc, sys.monitoring, importtime, and perf.
- [Interpreter](references/interpreter.md): lookups, comprehensions, C
  methods, generators, strings, keys, regex, and caches.
- [Containers](references/containers.md): sets, deque, Counter, bisect,
  heapq, slots, array, memoryview, bytearray, and struct.
- [Concurrency](references/concurrency.md): processes, threads, asyncio,
  subinterpreters, and free-threading.
- [Runtime](references/runtime.md): specialization, the JIT, and deferred
  imports.

## Completion evidence

The final report contains:

- the interpreter (`python -VV`), the GIL or free-threaded build, JIT
  state, OS and CPU, and the project's supported Python range;
- the profile, trace, or import-time output that attributed the cost;
- the construct applied, with its **Use when** conditions checked;
- the oracle command and its result, including edge cases;
- the card's deterministic metric before and after;
- pyperf `compare_to` rows (mean ± std dev and significance) from the same
  machine and interpreter, plus the application-level result;
- anything not run, for example Linux `perf`, free-threaded builds, JIT
  builds, or other Python versions, stated as not verified.
