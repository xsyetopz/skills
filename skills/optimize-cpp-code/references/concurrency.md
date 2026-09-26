# Concurrency constructs

Cards that remove memory-ordering fences, cache-line contention, shared
atomic traffic, and serial work. Pairs live in
[`constructs/concurrency.cpp`](../assets/examples/constructs/concurrency.cpp);
the parallel-algorithm program is
[`standalone/parallel.cpp`](../assets/examples/standalone/parallel.cpp).
`verify.sh verify` checks totals and a release/acquire handoff;
`verify.sh asm` asserts the atomic instructions; `verify.sh time` and
`verify.sh parallel` time the rest.

Measured numbers are machine-specific: Apple M1 Max (8 performance and 2
efficiency cores, `hw.cachelinesize` 128), macOS 27.0 arm64, Apple
clang 21.0.0, libc++ 21.1, `-std=c++23 -O2`, four threads per
contention pair. The machine was heavily shared (load average 40 to
70), and multi-threaded medians varied several-fold between runs, so
only large ratios are reported. Rerun on an idle machine before quoting.

These cards cover the C++ memory model API.

## Contents

- memory_order_relaxed for event counters
- Acquire and release instead of seq_cst for publication
- Padding per-thread data against false sharing
- hardware_destructive_interference_size
- Per-thread accumulation instead of a shared atomic
- Parallel algorithms with std::execution::par

## memory_order_relaxed for event counters

**Definition.** An atomic operation is indivisible at any memory order;
`memory_order_relaxed` drops only the ordering guarantees for other
memory ([atomics.order]). `fetch_add` and `++` default to
`memory_order_seq_cst`. On arm64 with LSE atomics, clang emits `ldaddal`
(acquire+release) for seq_cst and `ldadd` for relaxed.

**Use when.**

- The counter is a statistic or an ID generator, read only after the
  threads join or read without implying anything about other data.

**Do not use when.**

- Another thread reads the counter to decide that data written before
  the increment is ready (a reference count reaching zero before
  `delete`, a "work done" count): that needs release on the writer and
  acquire on the reader. `std::shared_ptr` uses acq_rel for this reason
  (see the objects cards).
- The rewrite splits `fetch_add` into a separate `load` and `store`:
  that is no longer atomic, and two threads can lose an increment even
  with seq_cst.

**Example.**

```cpp
long bump_relaxed_candidate(std::atomic<long> &c) {
  return c.fetch_add(1, std::memory_order_relaxed); // ldadd
}
// baseline: return c.fetch_add(1); // seq_cst: ldaddal
```

Runnable: `assets/examples/constructs/concurrency.cpp`.

**Cost removed.** Acquire/release semantics on each increment. Measured:
`ASM bump_seq_cst_baseline: 1 line(s) match /ldaddal/`,
`bump_relaxed_candidate: 0`; 1000 uncontended increments 7.25 -> 2.15
µs (single thread).

**Verify.**

1. `verify.sh verify` checks the total after both forms.
1. `verify.sh asm` asserts `ldaddal` versus `ldadd`.

## Acquire and release instead of seq_cst for publication

**Definition.** A release store and an acquire load that reads its
value create a happens-before edge: writes before the store are visible
after the load ([atomics.order]). seq_cst adds one total order over
all seq_cst operations, which one-producer publication does not need.

**Use when.**

- A flag or pointer publishes data from one thread to others
  (`ready.store(1)` after filling a buffer, readers spin on
  `ready.load()`).

**Do not use when.**

- The algorithm needs one total order across different atomics
  (Dekker-style mutual exclusion: each thread stores its own flag, then
  loads the other's). Release/acquire lets both threads see the old
  value; keep seq_cst.
- You expect a speedup on arm64 stores: both forms emit `stlr` here.

**Example.**

```cpp
payload = 42;                                  // plain write
ready.store(1, std::memory_order_release);     // publish
while (ready.load(std::memory_order_acquire) == 0) {
}
long const seen = payload;                     // guaranteed 42
```

Runnable: `assets/examples/constructs/concurrency.cpp`.

**Cost removed.** On the load side only. Measured: the seq_cst load emits
`ldar` and the acquire load `ldapr` (RCpc; weaker, can be cheaper);
both stores emit `stlr` (no difference). Timing did not separate from
noise on this shared machine, so this is an assembly-level result.

**Verify.**

1. `verify.sh verify` runs the handoff and checks the payload.
1. `verify.sh asm` prints `ldar`, `ldapr`, and `stlr` counts.

## Padding per-thread data against false sharing

**Definition.** Threads writing different variables on one cache line
move the line between cores on every write (false sharing). Align each
per-thread slot to the line size.

**Use when.**

- Per-thread counters, queue heads and tails, or slots sit next to each
  other in an array or struct and different threads write them.

**Do not use when.**

- The data is read-mostly: padding wastes cache and memory for no
  gain.
- You would pad to 64 bytes on the M1 Max measured here: `sysctl -n
  hw.cachelinesize` reports 128, and 64-byte slots had 2 to 5 times
  worse medians than 128-byte slots in three runs (minimums tied in one
  run). Inferred, not measured: `alignas(64)` still puts two slots in
  each 128-byte line, so contention depends on which threads share a
  line. Check the line size on each target.

**Example.**

```cpp
template <std::size_t Align> struct alignas(Align) Padded {
  std::atomic<long> n{0};
};
std::vector<Padded<128>> slots(kThreads); // one line per thread
// baseline: struct Packed { std::atomic<long> n{0}; }; (8 bytes)
```

Runnable: `assets/examples/constructs/concurrency.cpp`.

**Cost removed.** Cache-line transfers. Measured medians (four threads,
200000 relaxed increments each), three runs:

| Layout | Run 1 median (min) | Run 2 median (min) | Run 3 median (min) |
| --- | --- | --- | --- |
| packed, 8 bytes | 10.5 ms (2.3) | 13.4 ms (3.5) | 11.3 ms (2.3) |
| 64-byte slots | 2.2 ms (1.14) | 2.5 ms (0.48) | 1.75 ms (1.08) |
| 128-byte slots | 0.49 ms (0.48) | 0.49 ms (0.48) | 0.87 ms (0.51) |
| 256-byte slots | 0.50 ms (0.48) | 0.62 ms (0.48) | 0.63 ms (0.48) |

Each run times packed again for every padded pair; the packed row
shows the first pair's baseline.

**Verify.**

1. `verify.sh verify` checks that every layout sums to 800000.
1. `verify.sh time false-sharing`; repeat when the machine is idle.

## hardware_destructive_interference_size

**Definition.** `std::hardware_destructive_interference_size` (C++17,
`<new>`, [hardware.interference]) is "the minimum recommended offset
between two concurrently-accessed objects to avoid additional
performance degradation due to contention introduced by the
implementation". libc++ ships it since version 19 ([libc++ C++17
status][libcxx-17]) and takes the value from the compiler macro
`__GCC_DESTRUCTIVE_SIZE`.

**Use when.**

- Code built for one target needs a padding size and would otherwise
  hard-code 64.

**Do not use when.**

- You assume it equals the hardware line: here it is 256 (and
  `hardware_constructive_interference_size` is 64) while
  `hw.cachelinesize` is 128. Measured: `INTERFERENCE: destructive 256,
  constructive 64, sizeof Interference 256`. It quadruples per-slot
  memory against the 64-byte guess and doubles it against the measured
  need.
- The struct appears in a public header or a serialized layout: the
  value is a compile-time constant from the compiler, so builds with a
  different compiler or target can disagree on `sizeof` and field
  offsets (an ABI mismatch). This is inferred from how the value is
  defined, not observed. Use an explicit number in shared layouts.

**Example.**

```cpp
struct Interference {
  alignas(std::hardware_destructive_interference_size)
      std::atomic<long> n{0};
};
```

Runnable: `assets/examples/constructs/concurrency.cpp`.

**Cost removed.** Same as the padding card; measured 256-byte slots were
not faster than 128-byte slots.

**Verify.**

1. `c++ -std=c++23 -dM -E -x c++ /dev/null | grep INTERFERENCE`
   prints nothing; `grep DESTRUCTIVE` shows the macro (256 here).
1. `verify.sh verify` prints the `INTERFERENCE` line.

## Per-thread accumulation instead of a shared atomic

**Definition.** Each thread accumulates into a local variable and
combines once at the end; the shared atomic sees one write per thread
instead of one per item.

**Use when.**

- Threads update one shared counter, sum, or histogram per item.

**Do not use when.**

- Other threads need the running value during the work (progress bars,
  rate limits): publish partial sums periodically instead.
- The combine step is not associative for the type (floating-point
  sums): the result changes with thread count and scheduling. State
  that, or use a deterministic reduction order.

**Example.**

```cpp
ts.emplace_back([&total] {
  long local = 0;
  for (long i = 0; i < kIters; ++i) local += 1;
  total.fetch_add(local, std::memory_order_relaxed); // once
});
```

Runnable: `assets/examples/constructs/concurrency.cpp`.

**Cost removed.** Contended atomic writes. Measured: 11.6 ms -> 0.18 ms
(four threads, 200000 items each; medians on a loaded machine).

**Verify.**

1. `verify.sh verify` checks that both totals equal 800000.
1. `verify.sh time local-accumulate`.

## Parallel algorithms with std::execution::par

**Definition.** Standard algorithms take an execution policy
([algorithms.parallel]); `std::execution::par` allows execution on
multiple threads. In libc++ they are experimental: the user
documentation lists "The parallel algorithms library (`<execution>` and
associated algorithms)" as enabled only by `-fexperimental-library`
([libc++ user documentation][libcxx-user]), and P0024R2 is "In
Progress" ([libc++ C++17 status][libcxx-17]). The SDK's libc++ is
configured with the libdispatch backend
(`_LIBCPP_PSTL_BACKEND_LIBDISPATCH` in `__config_site`).

**Use when.**

- One large, independent operation dominates (sorting or transforming
  millions of elements), and either the build may use experimental
  libc++ features or the target's standard library has them stable.

**Do not use when.**

- Inputs are small: measured `std::sort` par was slower at 1000 and
  100000 elements.
- The operation is memory-bound: measured `transform_reduce` par was
  slower at every size (10 M elements: seq 0.86 ms, par 1.65 ms).
- The code must build without `-fexperimental-library`: without it,
  `std::execution::par` does not exist ("no member named 'par'").
  `__cpp_lib_execution` stays undefined even with the flag.
- `std::reduce` is fed elements narrower than the init type: reduce may
  add two elements directly ([numerics.defns] GENERALIZED_SUM), so
  `reduce(par, unsigned*, ..., 0ULL)` wraps in 32 bits. Measured:
  `reduce(par, unsigned, 0ULL) DIFFERS FROM accumulate` at every size.
  Widen with `transform_reduce`.
- Element access functions throw: with `par`, an escaping exception
  calls `std::terminate` ([algorithms.parallel.exceptions]).

**Example.**

```cpp
std::sort(std::execution::par, v.begin(), v.end());
auto const total = std::transform_reduce(
    std::execution::par, v.begin(), v.end(), 0ULL,
    std::plus<unsigned long long>{},
    [](unsigned x) { return static_cast<unsigned long long>(x); });
```

Runnable: `assets/examples/standalone/parallel.cpp`.

**Cost removed.** Wall time for large sorts only. Measured, 10 M random
`unsigned`: `std::sort` seq 513.9 ms, par 283.7 ms; 100000 elements:
seq 1.95 ms, par 2.48 ms. A rerun under heavier load: 10 M seq
1251.1 ms, par 294.5 ms; 100000 seq 2.53 ms, par 2.87 ms.

**Verify.**

1. `verify.sh parallel` checks that sorted output and widened sums
   equal the sequential results before printing times.
1. Compare the printed medians per size; keep `par` only at sizes where
   it wins on the target.

[atomics.order]: https://eel.is/c++draft/atomics.order
[hardware.interference]: https://eel.is/c++draft/hardware.interference
[libcxx-17]: https://libcxx.llvm.org/Status/Cxx17.html
[algorithms.parallel]: https://eel.is/c++draft/algorithms.parallel
[libcxx-user]: https://libcxx.llvm.org/UserDocumentation.html
[numerics.defns]: https://eel.is/c++draft/numerics.defns
[algorithms.parallel.exceptions]: https://eel.is/c++draft/algorithms.parallel.exceptions
