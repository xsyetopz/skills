# Measurement constructs

Correctness oracles, timing, profiling, allocation tracing, event counting,
and import-time measurement. Runnable code:
[`measurement.py`](../assets/examples/constructs/measurement.py),
[`check.py`](../assets/examples/constructs/check.py), and
[`bench.py`](../assets/examples/constructs/bench.py). Run
`sh assets/examples/verify.sh verify` for the oracles and
`sh assets/examples/verify.sh measure` for pyperf timing.

Tier: Executed (`sh assets/examples/verify.sh verify` and `measure`),
except the perf trampoline card, which is not runnable here. Measured
numbers are machine-specific: Apple M1 Max, macOS, Homebrew CPython 3.14.7
(GIL build, no JIT), pyperf 2.10.0. Counts of calls, instructions, and traced
bytes are deterministic for a given CPython version and input; timings do not
carry over to other machines.

## Contents

- Differential equivalence oracle
- timeit with the minimum of repeats
- pyperf Runner.bench_func
- pyperf timeit command
- pyperf compare_to
- cProfile and pstats
- tracemalloc peak as an allocation oracle
- tracemalloc snapshot diff
- sys.monitoring call counter
- Executed-instruction counting
- python -X importtime
- Linux perf trampoline

## Differential equivalence oracle

**Definition.** A test that runs baseline and candidate on the same inputs
(empty, boundary, one-shot iterator, tuple, duplicate, and error cases) and
asserts identical results. It is the only evidence that a faster candidate
still does the same work.

**Use when.**

- Always, before any timing: every card in this skill starts from it.
- The candidate changes the data structure, evaluation order, laziness, or
  exception path.

**Do not use when.**

- The inputs are only `list`s: the oracle misses a candidate that consumes a
  one-shot iterator twice (`list(values)` followed by a second pass), and the
  bug ships.
- The results are equal only by accident: `set` iteration order can match
  input order for small integers. Include inputs whose order differs, such as
  `[3, 1, 3, 2, 1]`.

**Example.**

```python
def differential(name, baseline, candidate):
    cases = [[], [0], [3, 1, 3, 2, 1], [5, -5, 0, 5]]
    for case in cases:
        check.equal(name, baseline(list(case)), candidate(list(case)))
        check.equal(name, baseline(iter(case)), candidate(iter(case)))
        check.equal(name, baseline(tuple(case)), candidate(tuple(case)))
```

Runnable: `differential` and `rejects` in `measurement.py`. The oracle accepts
`list(dict.fromkeys(values))` as an order-preserving unique operation and
rejects `list(set(values))` (order changes) and a candidate that exhausts an
iterator.

Add cases for these semantic traps when they apply:

- falsy values (`0`, `""`, `False`) against `x or default`;
- `max`/`min` tie order (`max` returns the first maximal item, per the
  [`max` docs][max]);
- float summation: `sum` uses Neumaier compensated summation for floats since
  3.12 ([What's New 3.12][wn312]), so a manual loop is not equivalent;
- `except BaseException` or bare `except` in a fast path swallows
  `KeyboardInterrupt` and `asyncio.CancelledError`;
- `[[0]] * n` aliases one inner list n times.

**Cost removed.** Rework, not time: a wrong candidate fails before it is
timed. The script prints `ORACLE rejected <name>` for each broken variant.

**Verify.**

1. `sh assets/examples/verify.sh verify` must print `ORACLE rejected
   set-order` and `ORACLE rejected iterator-consumed`, then `PASSED`.
1. In the target project, the oracle test must pass under the project's test
   runner before and after the change.

## timeit with the minimum of repeats

**Definition.** `timeit.Timer(stmt).autorange()` raises the loop count
through 1, 2, 5, 10, 20, 50, ... until one measurement takes at least 0.2 s.
`repeat(repeat, number)` returns the raw totals. `timeit` disables garbage
collection while timing ([timeit docs][timeit]).

**Use when.**

- You compare two snippets quickly in one interpreter while iterating.
- The statement runs in microseconds to milliseconds and has no warmup phase
  to separate.

**Do not use when.**

- The result is evidence for a decision: use pyperf, which spawns worker
  processes and reports the spread.
- The cost includes GC and `setup` lacks `gc.enable()`: timeit turns GC off
  by default, so allocation-heavy code looks faster than it is (the timeit
  docs show the fix).
- You would report the mean: the minimum "is probably the only number you
  should be interested in".

**Example.**

```python
import timeit

def timeit_min_seconds(stmt):
    timer = timeit.Timer(stmt)
    loops, _ = timer.autorange()
    runs = timer.repeat(repeat=5, number=loops)
    return min(runs) / loops  # seconds per call
```

CLI form: `python -m timeit -s 'from mod import f, data' 'f(data)'`. Default
repeat count: 5. `-p` measures process time instead of wall time.

**Cost removed.** None; this card measures cost. Measured: `word_counts`
over 500 lines took 569.6 us/call (min of 5; machine-specific, see the top of
this file).

**Verify.**

1. `verify.sh verify` prints `METRIC timeit word_counts: ... us/call`.
1. Before recording a timeit number, confirm both snippets return equal
   results (oracle card).

## pyperf Runner.bench_func

**Definition.** `pyperf.Runner().bench_func(name, func, *args)` calibrates
the loop count, runs worker processes, collects warmups and values, and with
`-o` writes JSON with metadata. pyperf 2.10.0 defaults for CPython without a
JIT: 20 processes, 3 values per process, 1 warmup. `--fast` halves the
process count (minimum 3); `--rigorous` doubles it
([runner docs][pyperf-runner], [`_runner.py`][pyperf-runner-src]).

**Use when.**

- You need a keep-or-revert decision on one function pair, with baseline
  and candidate under identical interpreter, input, and process
  conditions.

**Do not use when.**

- The benchmark name differs between variants: `compare_to` cannot pair the
  rows.
- Setup sits inside the timed callable: build inputs outside `bench_func`,
  or they are timed too.
- Custom options reach only the parent process: pass them to workers through
  `add_cmdline_args`, or each worker times the default variant.
- The workload reads environment variables: workers get a reduced
  environment (`PATH`, `HOME`, `PYTHONPATH`, `PYTHON_GIL`, and a few others in
  pyperf 2.10.0). Pass `--inherit-environ NAME,...`
  ([`create_environ`][pyperf-env]).

**Example.**

```python
def add_worker_args(cmd, args):
    cmd.extend(("--variant", args.variant))

runner = pyperf.Runner(add_cmdline_args=add_worker_args)
runner.argparser.add_argument("--variant", required=True)
args = runner.parse_args()
func = candidate if args.variant == "candidate" else baseline
runner.bench_func("str_join", func, parts)
```

Runnable: `bench.py`. It asserts `baseline(*inputs) == candidate(*inputs)`
before timing and exits with an error if they disagree.

**Cost removed.** None; this card measures cost. It turns noisy single
timings into distributions and flags unstable runs.

**Verify.**

1. `PYTHON=<python with pyperf> sh assets/examples/verify.sh benchmark` runs
   every pair once per variant with `--debug-single-value`: a harness smoke
   test, not a timing result.
1. `verify.sh measure` writes `baseline.json` and `candidate.json` under
   `BENCH_OUT`. `python -m pyperf check <file>` then warns when the standard
   deviation exceeds 10% of the mean or a raw value is under 1 ms
   ([pyperf CLI][pyperf-cli]).

## pyperf timeit command

**Definition.** `python -m pyperf timeit -s SETUP STMT` is the pyperf form of
`timeit`. It accepts the same Runner options (`-o`, `--fast`, `--rigorous`,
`-p`) and can compare interpreters with `--compare-to` ([pyperf
CLI][pyperf-cli]).

**Use when.**

- The code under test is an importable expression that needs no harness
  script.
- You compare one statement under two interpreters, such as 3.13 and 3.14 or
  GIL and free-threaded.

**Do not use when.**

- The statement mutates the setup state, so every loop sees different input:
  use `bench_func` with fresh inputs, or make the operation idempotent.
- The candidate needs an import path the baseline lacks: time both through
  the same module.

**Example.**

```sh
python -m pyperf timeit --fast -o base.json \
  -s 'from interpreter import baseline_render as f; p=["ab"]*20000' \
  'f(p)'
python -m pyperf timeit --fast -o cand.json \
  -s 'from interpreter import candidate_render as f; p=["ab"]*20000' \
  'f(p)'
python -m pyperf compare_to base.json cand.json --table
```

Run from `assets/examples/constructs` so the modules import.

**Cost removed.** None; this card measures cost. The compare_to card makes
the decision.

**Verify.**

1. Both commands exit 0 and write JSON.
1. The `compare_to` table lists one row with both values and a significance
   verdict.

## pyperf compare_to

**Definition.** `python -m pyperf compare_to ref.json new.json --table`
pairs benchmarks by name and prints mean ± std dev and the speed ratio. A
difference is "not significant" when a two-sample, two-tailed Student t-test
does not separate the samples. `--min-speed` sets a minimum
percentage ([pyperf CLI][pyperf-cli]).

**Use when.**

- You decide whether to keep a candidate: keep it only when the target row is
  significant in the intended direction and no other row regressed.

**Do not use when.**

- The two files come from different machines, interpreters, or pyperf
  options: the ratio is meaningless.
- The target row is "Not significant": do not keep the candidate on it.
  Report no measurable change, never a win.

**Example.** The `measure` mode of `verify.sh` runs:

```sh
python -m pyperf compare_to "$OUT/baseline.json" \
  "$OUT/candidate.json" --table
```

**Cost removed.** False keeps. Reading the output:

- By default, `--table` hides rows that are not significant and ends with
  `Benchmark hidden because not significant (N): ...`. A missing row means
  "no measurable change", not "not run".
- `Ignored benchmarks (N) of X.json` means those names exist in only one
  file. Treat it as a failed run and repeat both variants into a fresh
  directory. Observed locally: a first run into a directory another process
  was writing produced exactly this output and was discarded.
- The construct cards record measured `--fast` rows such as
  `str_join 87.1 ms -> 102 us, 855.02x faster` and
  `hoist_method 85.3 us -> 90.2 us, 1.06x slower`, labeled
  machine-specific.

**Verify.**

1. `BENCH_OUT=/tmp/b PYPERF_ARGS=--fast sh assets/examples/verify.sh
   measure` ends with a table and `Results: /tmp/b`.
1. `python -m pyperf stats /tmp/b/candidate.json` shows the value count,
   median, and outlier count behind each row.

## cProfile and pstats

**Definition.** `cProfile` is a deterministic profiler: it records every
call and return, with `ncalls`, `tottime` (own time), and `cumtime`
(including callees). `pstats.Stats` sorts and prints the results
(`sort_stats("cumulative")`, `print_callers`) ([profile docs][profile]).

**Use when.**

- You need the Python functions that dominate a workload before choosing a
  card.
- You need exact call counts, for example to show that a cache or a
  precompiled pattern removed calls.

**Do not use when.**

- You would compare timings from a profiled run: the profiler adds overhead
  to Python calls but not to C calls, so C code looks cheaper. The profiler
  is "not for benchmarking".
- The time is in native extensions or waiting: cProfile sees only the
  calling frame. Use a sampling profiler the project already approves, or
  `perf` on Linux (perf trampoline card).
- The code relies on `sys.monitoring` tool id 2: on 3.12+ cProfile holds
  `PROFILER_ID` while enabled (observed locally:
  `sys.monitoring.get_tool(2)` returns `'cProfile'`).

**Example.**

```python
profiler = cProfile.Profile()
profiler.enable()
try:
    word_counts(LINES)
finally:
    profiler.disable()
stats = pstats.Stats(profiler, stream=io.StringIO())
stats.sort_stats("cumulative").print_stats(8)
```

CLI form: `python -m cProfile -o out.prof -s cumulative app.py`; read the file
with `python -m pstats out.prof`.

**Cost removed.** None by itself; it finds the function that owns the cost.
The oracle asserts that `tokenize` was called exactly
`len(LINES)` times and `normalize` once per token.

**Verify.**

1. `verify.sh verify` passes `cprofile/tokenize ncalls` and
   `cprofile/normalize ncalls`.
1. Profile again after the change: the targeted function's `ncalls` or
   `tottime` must drop, not just move to a callee.

## tracemalloc peak as an allocation oracle

**Definition.** `tracemalloc.start()` hooks Python's memory allocators.
`get_traced_memory()` returns `(current, peak)` bytes of traced blocks, and
`reset_peak()` (3.9+) moves the peak back to the current value. Only
Python's allocators are traced, not native allocators that extensions use
([tracemalloc docs][tracemalloc]).

**Use when.**

- The claim is "uses less memory": temporary lists, copies, per-instance
  dictionaries.
- You need a deterministic assertion: the traced peak repeats for the same
  CPython version and input.

**Do not use when.**

- NumPy, a database driver, or other native code allocates the memory: it
  does not appear in the trace. Measure process RSS instead, for example
  `resource.getrusage(...).ru_maxrss` or pyperf `--track-memory`.
- You would time code while tracemalloc is active: tracing slows every
  allocation.

**Example.**

```python
def peak_bytes(action):
    action()  # warm caches, interned strings, lazy imports
    gc.collect()
    tracemalloc.start()
    try:
        action()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
```

Runnable: `peak_bytes` in `check.py`, used by the generator, heapq.merge,
slots, array, and memoryview cards.

**Cost removed.** None by itself; it exposes the bytes other cards remove.
Measured: `sum([x*x for x in range(200_000)])` peaks at 8,023,696 B, the
generator form at 512 B.

**Verify.**

1. `verify.sh verify` prints `METRIC <card> tracemalloc peak B: a -> b` with
   `b < a` for each memory card.
1. Rerun with the input size doubled: the baseline peak must grow and the
   streaming candidate's peak stay flat.

## tracemalloc snapshot diff

**Definition.** `take_snapshot()` captures all traced blocks.
`after.compare_to(before, "lineno")` returns `StatisticDiff` rows grouped by
file and line, sorted by size change. `filter_traces([Filter(True,
pattern)])` restricts the rows to your files ([tracemalloc docs][tracemalloc]).

**Use when.**

- Memory grows and the allocating line is unknown.
- You hunt a leak: objects kept alive between two points.

**Do not use when.**

- The allocating frame is deeper than the traceback limit: `start()` stores
  one frame by default. Use `start(25)` or `-X tracemalloc=25` to group by
  traceback.
- The result is discarded before the second snapshot: freed blocks do not
  show up. Keep a reference until after `take_snapshot()`.

**Example.**

```python
tracemalloc.start()
before = tracemalloc.take_snapshot()
kept = build_index(20_000)
after = tracemalloc.take_snapshot()
tracemalloc.stop()
only_here = [tracemalloc.Filter(True, __file__)]
top = after.filter_traces(only_here).compare_to(
    before.filter_traces(only_here), "lineno")[0]
```

**Cost removed.** None; the diff attributes growth to a line. The oracle
asserts that the top row is the dictionary comprehension line in
`build_index`.

**Verify.**

1. `verify.sh verify` passes `tracemalloc-diff/file` and
   `tracemalloc-diff/line`.
1. After the fix, the same diff must drop the line from the top or shrink its
   `size_diff`.

## sys.monitoring call counter

**Definition.** `sys.monitoring` (3.12+, PEP 669) lets a tool claim an id
(0–5) with `use_tool_id`, register callbacks with `register_callback`, and
turn events on with `set_events`. `PY_START` fires when a Python function
starts, with `(code, instruction_offset)`
([sys.monitoring docs][monitoring]).

**Use when.**

- You need exact Python-call counts per function without cProfile's timing
  overhead, for example to show that `itemgetter` removed lambda calls.
- You build a small custom profiler or coverage probe.

**Do not use when.**

- The Python version is below 3.12: the module does not exist. Use
  `sys.setprofile` or cProfile.
- You would hard-code `PROFILER_ID` (2): cProfile holds it while enabled, and
  `use_tool_id` raises `ValueError` for an id in use. Pick a free id with
  `get_tool(id) is None`.
- A global-event callback would return `sys.monitoring.DISABLE`: this raises
  `ValueError`. It is valid only for local events.

**Example.**

```python
mon = sys.monitoring
tool = next(t for t in range(6) if mon.get_tool(t) is None)
counts = Counter()

def on_start(code, offset):
    counts[code.co_qualname] += 1

mon.use_tool_id(tool, "call-counter")
try:
    mon.register_callback(tool, mon.events.PY_START, on_start)
    mon.set_events(tool, mon.events.PY_START)
    word_counts(LINES)
finally:
    mon.set_events(tool, mon.events.NO_EVENTS)
    mon.free_tool_id(tool)
```

**Cost removed.** None by itself. `python_calls` in `check.py` uses it to
prove the itemgetter-key (3001 -> 1 Python calls) and re-compile
(4001 -> 1) claims.

**Verify.**

1. `verify.sh verify` passes `sys.monitoring/tokenize` and
   `sys.monitoring/normalize`. The counts equal cProfile's `ncalls`.
1. The tool id must be released: after the call,
   `sys.monitoring.get_tool(tool)` is `None`.

## Executed-instruction counting

**Definition.** The `INSTRUCTION` event of `sys.monitoring` (3.12+) fires
before each bytecode instruction with `(code, offset)`. Mapping the offset
through `dis.get_instructions(code)` gives the base opname, so the count of
executed
`LOAD_ATTR`, `LOAD_GLOBAL`, `CALL`, or all instructions is exact for one call
([sys.monitoring][monitoring], [dis][dis]).

**Use when.**

- The claim is at the bytecode level: fewer attribute or global loads,
  calls, or Python-level loop iterations.
- Timing differences are too small to be significant; the executed count
  still shows the mechanism.

**Do not use when.**

- You would treat a count as a speedup: the 3.11+ specializing interpreter
  caches many `LOAD_GLOBAL` and `LOAD_ATTR` sites, so a lower count does not
  always mean less time. Confirm with pyperf.
- You would compare counts across CPython versions: bytecode is an
  implementation detail with no compatibility guarantee ([dis][dis]). 3.14
  added `LOAD_FAST_BORROW`, so match opnames by prefix.

**Example.** `executed_ops` in `check.py`:

```python
def on_instruction(code, offset):
    nonlocal count
    table = names.get(code)
    if table is None:
        table = {i.offset: i.opname for i in dis.get_instructions(code)}
        names[code] = table
    if table.get(offset, "").startswith(prefixes):
        count += 1
```

**Cost removed.** None by itself. Measured counts for the cards that use it:
local binding 6,004 -> 2,006 `LOAD_ATTR`+`LOAD_GLOBAL`; `bytes.count` 168,597
-> 20 instructions.

**Verify.**

1. `verify.sh verify` prints the `executed` metrics for the local-binding,
   hoist-method, comprehension, builtin-method, and struct cards.
1. Recount on the project's own function: `executed_ops(lambda: f(x),
   ("LOAD_ATTR",))` before and after the change.

## python -X importtime

**Definition.** `-X importtime` (3.7+) or `PYTHONPROFILEIMPORTTIME=1` prints
one stderr line per import: `import time: self [us] | cumulative | name`.
Nested imports are indented. `-X importtime=2` (3.14+) also marks modules
that were already loaded as `cached` ([cmdline][cmdline]).

**Use when.**

- CLI start-up, serverless cold start, or test collection is slow.
- You need the import chain that loads heavy modules, before applying the
  deferred-import card in [runtime](runtime.md#deferred-import).

**Do not use when.**

- You would read one run: the first run compiles `.pyc` files. Take the
  minimum of several warm runs.
- The application imports from several threads: the docs warn the output
  may be broken.

**Example.**

```sh
python -X importtime -c 'import startup_eager' 2>&1 | tail -4
python -X importtime=2 -c 'import json, json' 2>&1 | grep cached
```

Runnable: `import_times` in `measurement.py` passes
`-X pycache_prefix=<tmpdir>` so no `__pycache__` lands in the source tree.

**Cost removed.** None; this card measures cost. Measured `verify.sh verify`
output, min of 5 warm runs with the bytecode cache in a temporary directory:
`startup_eager` 1,649 us cumulative and `startup_lazy` 219 us
(machine-specific).

**Verify.**

1. `verify.sh verify` asserts that `decimal` appears in the eager import list
   and not in the lazy one.
1. Compare the cumulative column of the top-level module before and after.

## Linux perf trampoline

**Definition.** On Linux builds with `HAVE_PERF_TRAMPOLINE`, `-X perf` (3.12+),
`PYTHONPERFSUPPORT=1`, or `sys.activate_stack_trampoline("perf")` writes a
perf map, so `perf report` shows Python function names in native stacks.
`-X perf_jit` (3.13+) works without frame pointers through DWARF and needs
perf 6.8+ ([perf howto][perf], [cmdline][cmdline]).

**Use when.**

- Time splits between Python and C extensions and you need one profile that
  shows both.
- The platform is Linux and `python -m sysconfig | grep HAVE_PERF_TRAMPOLINE`
  prints 1.

**Do not use when.**

- The platform is macOS or Windows. Observed locally on macOS: `-X perf`
  silently has no effect, and `sys.activate_stack_trampoline("perf")`
  raises `ValueError: perf trampoline not available`.
- The JIT is active: stack trampolines cannot be activated then ([sys
  docs][sys]).

**Example.**

```sh
perf record -F 9999 -g -o perf.data python -X perf app.py
perf report -g -i perf.data
```

For complete stacks, the howto recommends a CPython built with frame
pointers:

```sh
CFLAGS="-fno-omit-frame-pointer -mno-omit-leaf-frame-pointer"
```

**Cost removed.** None; the profile attributes native time to Python callers.

**Verify.** Tier: not runnable here (macOS; no `perf`). The user runs:

1. `python -c 'import sys; sys.activate_stack_trampoline("perf");
   print(sys.is_stack_trampoline_active())'` must print `True`.
1. `perf report` must list `py::<function>` frames.
   `perf_trampoline_roundtrip` in `runtime.py` runs step 1 automatically on
   Linux.

[cmdline]: https://docs.python.org/3/using/cmdline.html#cmdoption-X
[dis]: https://docs.python.org/3/library/dis.html
[max]: https://docs.python.org/3/library/functions.html#max
[monitoring]: https://docs.python.org/3/library/sys.monitoring.html
[perf]: https://docs.python.org/3/howto/perf_profiling.html
[profile]: https://docs.python.org/3/library/profile.html
[pyperf-cli]: https://pyperf.readthedocs.io/en/latest/cli.html
[pyperf-runner]: https://pyperf.readthedocs.io/en/latest/runner.html
[pyperf-env]:
  https://github.com/psf/pyperf/blob/2.10.0/pyperf/_utils.py
[pyperf-runner-src]:
  https://github.com/psf/pyperf/blob/2.10.0/pyperf/_runner.py
[sys]: https://docs.python.org/3/library/sys.html#sys.activate_stack_trampoline
[timeit]: https://docs.python.org/3/library/timeit.html
[tracemalloc]: https://docs.python.org/3/library/tracemalloc.html
[wn312]: https://docs.python.org/3/whatsnew/3.12.html#other-language-changes
