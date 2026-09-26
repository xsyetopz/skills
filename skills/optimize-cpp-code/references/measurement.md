# Measurement constructs

Cards for proving that a C++ change is equivalent and cheaper. The
runnable catalog is
[`assets/examples`](../assets/examples); `verify.sh` builds in a
temporary directory, so no binary or `.s` file lands in the skill.

Measured numbers in this skill are machine-specific: Apple M1 Max (10
cores), macOS 27.0 arm64, Apple clang 21.0.0 from the swift.org 6.3.3
toolchain reached through `/usr/bin/c++`, libc++ 21.1 (`_LIBCPP_VERSION`
210106) from `MacOSX26.5.sdk`, `-std=c++23 -O2`. Other build jobs shared
the machine (load average up to 43), so medians are noisy; deterministic
counts are not.

## Contents

- Toolchain and SDK record
- Optimization barrier (sink and clobber)
- std::chrono median harness
- Counting global operator new
- Copy and move counting type
- Call-counting hasher, comparator, and predicate
- Assembly inspection with -S
- Compiler diagnostics as evidence
- AddressSanitizer and UBSan oracle build
- hyperfine for whole-process comparisons
- Google Benchmark
- xctrace Time Profiler

## Toolchain and SDK record

**Definition.** The compiler, standard library, and SDK decide which
constructs exist and how they compile. On macOS the libc++ headers come
from the SDK (`-v` shows `.../MacOSX26.5.sdk/usr/include/c++/v1` first
in the search list), not from the compiler.

**Use when.**

- Always before measuring, and again whenever a card names a version
  boundary (`std::flat_map` needs libc++ 20+, `std::print` 18+,
  `from_chars` for `double` 20+).

**Do not use when.**

- Never skip it: a baseline built against one SDK and a candidate built
  against another compare two standard libraries.

**Example.**

```sh
c++ --version
printf '#include <version>\nV _LIBCPP_VERSION\n' |
  c++ -std=c++23 -x c++ -E - | tail -1
echo '#include <version>' | c++ -std=c++23 -x c++ -E -v - 2>&1 |
  grep -A3 'search starts'
```

**Cost removed.** Wrong-library comparisons and invalid availability
claims. Measured: the default `MacOSX27.0.sdk` carries libc++ 22.1
headers (`220106`) but its `libSystem.B.tbd` fails to link on this
machine (`ld: tapi error: ... unknown architecture arm64e.x1-macos`), so
`verify.sh` falls back to the newest SDK that links a probe using
`<flat_map>` and `<print>` and prints the `SDKROOT` it chose. This is a
problem of this machine's toolchain, not of any construct.

**Verify.**

1. The first lines of every `verify.sh` mode show `c++ --version`
   (including `InstalledDir`), `SDKROOT=`, and `_LIBCPP_VERSION=`.
1. Record those three values in the report for both baseline and
   candidate.

## Optimization barrier (sink and clobber)

**Definition.** An empty `asm volatile` statement that takes a value as
an operand forces the compiler to materialize it; a `"memory"` clobber
forces pending writes to escaped memory. This is how Google Benchmark
implements `DoNotOptimize` and `ClobberMemory` ([user guide][gbench]).

**Use when.**

- A benchmark result is otherwise unused, or its input is a constant the
  optimizer could fold (`f(4096)`).
- An allocation-count check needs the allocated object to escape so the
  optimizer cannot remove a `new`/`delete` pair.

**Do not use when.**

- You need it for correctness: the guide says `DoNotOptimize(expr)` "does
  not prevent optimizations on `<expr>` in any way"; it only forces the
  result to exist.
- The barrier would go inside the measured function: it blocks
  optimizations the production code would get.

**Example.**

```cpp
template <class T> inline void sink(T const &value) {
  asm volatile("" : : "r,m"(value) : "memory");
}
inline void clobber() { asm volatile("" : : : "memory"); }
```

Runnable: `assets/examples/constructs/harness.hpp`.

**Cost removed.** False speedups from deleted work. Measured in
`standalone/parallel.cpp`: without a barrier between repetitions the
loop-invariant `transform_reduce` was hoisted and timed as `0.000 ms`.

**Verify.**

1. Every pair lambda in `constructs/*.cpp` passes its result to
   `h::sink`.
1. A candidate time near zero, or independent of input size, means the
   work was removed; inspect the assembly before believing it.

## std::chrono median harness

**Definition.** `h::time_pairs` calibrates a batch size until one batch
takes at least 200 µs, then records 31 batches with
`std::chrono::steady_clock` and prints the median and minimum ns per
call for baseline and candidate.

**Use when.**

- Google Benchmark is not installed or not allowed (here it is not
  installed: `brew list google-benchmark` reports no such keg).
- You need a quick paired comparison after the deterministic oracle
  passes.

**Do not use when.**

- The claim needs confidence intervals or change detection: this
  harness has no outlier analysis. Use Google Benchmark with
  `--benchmark_repetitions`.
- The machine is shared and the difference is under the run-to-run
  spread: rerun the pair alone (`verify.sh time NAME`) and report both
  runs.

**Example.**

```cpp
Timing measure(std::function<void()> const &f) {
  long batch = 1;
  while (ns_per_call(f, batch) * batch < 200'000.0 && batch < (1L << 24))
    batch *= 2;
  std::vector<double> samples;
  for (int i = 0; i < 31; ++i) samples.push_back(ns_per_call(f, batch));
  std::sort(samples.begin(), samples.end());
  return {samples[samples.size() / 2], samples.front()};
}
```

Runnable: `assets/examples/constructs/harness.cpp`.

**Cost removed.** Guesswork about timing; nothing in the program. The
`std::function` call adds the same indirect call to both sides of a
pair.

**Verify.**

1. `sh assets/examples/verify.sh time` prints one `TIME` line per pair.
1. `sh assets/examples/verify.sh time reserve` reruns one pair. Compare
   medians and minimums across two runs before reporting a difference.

## Counting global operator new

**Definition.** A program may replace the global allocation functions
([replacement.functions]); the harness replaces all of them (scalar,
array, nothrow, aligned, sized and aligned delete forms) and counts
calls with a relaxed atomic.

**Use when.**

- A card claims fewer allocations (reserve, string_view, pmr,
  make_shared, heterogeneous lookup).

**Do not use when.**

- The build uses AddressSanitizer: the ASan runtime interposes
  `operator new`, so allocations made inside `libc++.dylib` bypass the
  replacement. Measured: `sink-param-rvalue` counted `2 -> 1` normally and
  `1 -> 1` under ASan. `verify.sh sanitize` sets
  `CONSTRUCTS_NO_COUNTS=1` to keep the equality oracles and skip counts.
- You want an exact expected count for the baseline: clang may elide a
  `new`/`delete` pair. Assert only that the candidate is lower in the
  same run.

**Example.**

```cpp
std::atomic<long> g_calls{0};
void *operator new(std::size_t n) {
  g_calls.fetch_add(1, std::memory_order_relaxed);
  if (void *p = std::malloc(n == 0 ? 1 : n)) return p;
  throw std::bad_alloc{};
}
void operator delete(void *p) noexcept { std::free(p); }
// ... plus new[], nothrow, align_val_t, and sized delete forms
template <class F> long allocs(F &&f) {
  long const before = g_calls.load(std::memory_order_relaxed);
  f();
  return g_calls.load(std::memory_order_relaxed) - before;
}
```

Runnable: `assets/examples/constructs/harness.cpp`.

**Cost removed.** None; it measures allocation calls. `h::less` fails
the run unless the candidate count is strictly lower.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints `ALLOC name: B -> C`.
1. Over-aligned types (`alignas(256)` slots in `concurrency.cpp`) use
   the aligned overloads; the run passes only if those are replaced
   too.

## Copy and move counting type

**Definition.** `h::Tracked<NoexceptMove>` holds an `int` and increments
global counters in its copy and move operations; the template parameter
chooses whether the move constructor is `noexcept`.

**Use when.**

- A card claims that a copy became a move or that a move disappeared
  (elision, NRVO, `emplace_back`, `noexcept` growth, `erase_if`).

**Do not use when.**

- The production type's copy cost is what matters (a large
  `std::string` or `std::vector`): also count allocations of the real
  type.

**Example.**

```cpp
template <bool NoexceptMove> struct Tracked {
  int value = 0;
  explicit Tracked(int v) : value(v) {}
  Tracked(Tracked const &o) : value(o.value) { ++tracked.copies; }
  Tracked(Tracked &&o) noexcept(NoexceptMove) : value(o.value) {
    ++tracked.moves;
  }
  // assignment operators count the same way
};
```

Runnable: `assets/examples/constructs/harness.hpp`.

**Cost removed.** None; it measures copies and moves and prints
`COPIES name: B -> C` or `MOVES name: B -> C`.

**Verify.**

1. `verify.sh verify` prints the lines and fails unless the candidate
   is lower.
1. Cards that expect no difference use `h::same`, which fails when the
   counts differ.

## Call-counting hasher, comparator, and predicate

**Definition.** A hash functor, comparison, or predicate that increments
a counter before its real work turns "fewer lookups", "fewer
comparisons", or "lazy evaluation" into a number.

**Use when.**

- A card removes repeated hashing (`try_emplace`), comparisons
  (`partial_sort`), or predicate calls (ranges views).

**Do not use when.**

- Threads share the counter and it is not atomic: parallel algorithms
  need `std::atomic<long>` with relaxed increments.

**Example.**

```cpp
long g_hashes = 0;
struct CountingHash {
  std::size_t operator()(std::string const &s) const {
    ++g_hashes;
    return std::hash<std::string>{}(s);
  }
};
```

Runnable: `assets/examples/constructs/containers.cpp`.

**Cost removed.** Measured: `HASHES try-emplace: 599 -> 351`,
`COMPARES partial-sort-top-k: 150206 -> 10402`,
`PREDICATE ranges-lazy: 1000 -> 11`.

**Verify.**

1. `verify.sh verify` prints the three lines above.
1. The same oracle compares results before it compares counts.

## Assembly inspection with -S

**Definition.** `c++ -S` writes the assembly of one translation unit.
Mark the functions under test `extern "C"` and `noinline` to give them
stable names (Mach-O adds a leading `_`), so a script can extract one
function and count instruction patterns.

**Use when.**

- A card claims a change in generated code: an indirect call (`blr`)
  removed, an atomic (`ldadd`, `ldaddal`) removed or weakened, a guard
  (`__cxa_guard_acquire`) removed, a bounds trap (`brk`) added.

**Do not use when.**

- The flags differ from the timed build: `verify.sh` uses the same
  `-std=c++23 -O2` for both.
- The patterns are for another architecture (x86 on arm64 or the
  reverse): `verify.sh asm` prints `NOT ASSERTED` on non-aarch64 hosts.

**Example.**

```sh
c++ -std=c++23 -O2 -S constructs/codegen.cpp -o codegen.s
awk '$0 ~ "^_?virtual_total_baseline:" {on=1} on {print}
     on && /\.cfi_endproc/ {exit}' codegen.s | grep -c blr
```

**Cost removed.** Speculation about what the compiler did. Measured
results are in the codegen, objects, and concurrency cards.

**Verify.**

1. `sh assets/examples/verify.sh asm` ends with `ASM PASSED`.
1. Each `ASM name: N line(s) match /re/` line is the evidence to quote.

## Compiler diagnostics as evidence

**Definition.** Clang warns about some performance anti-patterns:
`-Wpessimizing-move` (a `std::move` that prevents copy elision),
`-Wredundant-move`, and `-Wdangling-gsl` (a view bound to a temporary
owner) ([Clang diagnostics reference][clang-diag]).

**Use when.**

- A diff adds `std::move` to `return` statements or stores a
  `std::string_view` or `std::span` into a variable.

**Do not use when.**

- You need proof of absence: `-Wdangling-gsl` catches only simple
  temporaries. Run the sanitizer build for lifetimes that cross
  functions.

**Example.**

```sh
c++ -std=c++23 -Wpessimizing-move -Wredundant-move -fsyntax-only \
  -I constructs constructs/objects.cpp
```

**Cost removed.** Review rounds. Measured: the command prints three
warnings for the baseline functions in `objects.cpp` (lines 21, 34,
45); `standalone/dangling.cpp` triggers `-Wdangling-gsl` by default.

**Verify.**

1. `sh assets/examples/verify.sh diagnose` asserts the three messages
   and that `standalone/consteval_error.cpp` fails to compile.
1. Build the candidate with `-Wall -Wextra -Werror` (as `verify.sh`
   does) so the anti-pattern cannot come back silently.

## AddressSanitizer and UBSan oracle build

**Definition.** `-fsanitize=address` instruments memory accesses and
reports use-after-free, buffer overflow, and use-after-scope;
`-fsanitize=undefined` reports undefined behavior such as signed
overflow ([ASan][asan], [UBSan][ubsan]). The full sanitizer card is in
`optimize-c-code`; this card covers C++ view lifetimes.

**Use when.**

- A candidate introduces `std::string_view`, `std::span`, references
  into containers, or `pmr` arenas, whose lifetime bugs are silent in
  release builds.

**Do not use when.**

- You time or count allocations: instrumented builds change both (see
  the counting card).

**Example.**

```sh
c++ -std=c++23 -O1 -g -fsanitize=address,undefined \
  -fno-omit-frame-pointer -fno-sanitize-recover=undefined \
  -I constructs constructs/*.cpp -o constructs-asan
CONSTRUCTS_NO_COUNTS=1 ./constructs-asan verify
```

**Cost removed.** Undetected lifetime bugs. Measured:
`standalone/dangling.cpp` reports
`ERROR: AddressSanitizer: heap-use-after-free`; the catalog runs clean.

**Verify.**

1. `sh assets/examples/verify.sh sanitize` ends with `SANITIZE PASSED`.
1. The ASan report names the line that reads the dangling view.

## hyperfine for whole-process comparisons

**Definition.** [hyperfine][hyperfine] runs commands repeatedly and
reports mean ± σ, min/max, and relative speed; `-N` runs without a
shell and `--warmup` discards initial runs.

**Use when.**

- The construct affects a whole process: stdout buffering, stream
  synchronization, hardening mode, or build flags.

**Do not use when.**

- Output goes to a terminal: use `--output=pipe` or `--output=null` so
  terminal speed is not measured.

**Example.**

```sh
hyperfine --warmup 3 -N --output=pipe \
  './constructs print-endl 200000' './constructs print-newline 200000'
```

**Cost removed.** None; it makes per-process overhead visible (system
time rises with flushes). Measured numbers are in the io cards.

**Verify.**

1. `verify.sh verify` first checks that every printer produces the
   same bytes (`cksum`).
1. `sh assets/examples/verify.sh io` runs the comparison.

## Google Benchmark

**Definition.** Google Benchmark runs each registered function in a
`for (auto _ : state)` loop, sizes iterations automatically, and
supports `--benchmark_repetitions`, `--benchmark_filter`,
`--benchmark_min_time`, `--benchmark_out`, and
`--benchmark_out_format=json` ([user guide][gbench]).

**Use when.**

- The repository already has it, or the claim needs repetitions with
  aggregates and JSON output.

**Do not use when.**

- Input construction sits inside the timed loop: build it before the
  loop, or use `state.PauseTiming()` sparingly (it has its own cost).

**Example.**

```cpp
#include <benchmark/benchmark.h>
#include <vector>
static void BM_Reserve(benchmark::State &state) {
  auto const n = static_cast<int>(state.range(0));
  for (auto _ : state) {
    std::vector<long> v;
    v.reserve(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) v.push_back(i);
    benchmark::DoNotOptimize(v.data());
  }
}
BENCHMARK(BM_Reserve)->Arg(1000);
BENCHMARK_MAIN();
```

**Cost removed.** Same as the chrono harness, with statistics.

**Verify.** Tier: not runnable here (Google Benchmark is not
installed); these steps were not executed:

1. `brew install google-benchmark`, then
   `c++ -std=c++23 -O2 bm.cpp -lbenchmark -o bm`.
1. `./bm --benchmark_repetitions=10 --benchmark_out=bm.json
   --benchmark_out_format=json`.

## xctrace Time Profiler

**Definition.** `xcrun xctrace record --template 'Time Profiler'`
samples call stacks of a launched process into a `.trace` bundle;
`xctrace export` writes tables such as `time-profile` as XML. `perf`
does not exist on macOS.

**Use when.**

- You need to attribute CPU time to functions before choosing a card.

**Do not use when.**

- The build lacks symbols: frames show as addresses. Add `-g` to the
  same `-O2` build you are optimizing.

**Example.**

```sh
xcrun xctrace record --template 'Time Profiler' --output run.trace \
  --launch -- ./constructs time reserve
xcrun xctrace export --input run.trace \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' \
  > profile.xml
```

**Cost removed.** Profile-free guessing. Measured: xctrace 16.0 recorded
`./constructs time reserve` (the `-O2 -g` build) and exported a
`time-profile` table whose frames include `_xzm_xzone_malloc_tiny`,
`_malloc_zone_malloc`, and libc++'s `__hash_table::__emplace_unique`.

**Verify.**

1. `xcrun xctrace export --input run.trace --toc` lists
   `schema="time-profile"`.
1. After the change, the same export shows a lower sample count for the
   target frame.

[gbench]: https://github.com/google/benchmark/blob/main/docs/user_guide.md
[replacement.functions]: https://eel.is/c++draft/replacement.functions
[clang-diag]: https://clang.llvm.org/docs/DiagnosticsReference.html
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[ubsan]: https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
[hyperfine]: https://github.com/sharkdp/hyperfine
