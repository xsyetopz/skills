# C++ performance gotchas

Profile first with `perf record -g` and `heaptrack` for allocations (both
Linux), and Google Benchmark for the harness. Read the generated assembly
with `objdump -d -C` (or `-S` for `-g` builds) before assuming the compiler
missed something. Paste code into public Compiler Explorer only with the
user's approval or on a self-hosted instance. On Windows, profile with
Windows Performance Analyzer (ETW traces) and read MSVC output with
`dumpbin /disasm`.

## Contents

- [Measurement](#measurement)
- [Copies, moves, and allocation](#copies-moves-and-allocation)
- [Containers](#containers)
- [Virtual calls and atomics](#virtual-calls-and-atomics)
- [Build and I/O](#build-and-io)

## Measurement

- Mistake: a Google Benchmark loop whose result is unused. Fix: pass the
  result to `benchmark::DoNotOptimize(x)` and call
  `benchmark::ClobberMemory()` after writes through a pointer; otherwise
  the optimizer removes the work. `DoNotOptimize` forces a value to exist
  in memory or a register, it does not prevent folding of constants that
  the compiler sees, so build inputs at runtime.
- Mistake: benchmarking a Debug or `-O0` build, or a build with
  `_GLIBCXX_ASSERTIONS` or `_LIBCPP_HARDENING_MODE` left on in only one
  side. Fix: identical production flags on both sides, including the
  hardening mode you ship.
- Mistake: one fixed input size. Fix: use `->Range(...)` or
  `->RangeMultiplier` so a cache-size cliff shows up; a win at 1 KiB often
  reverses at 10 MiB.
- Mistake: timing with a shared machine. Fix: pin the CPU
  (Linux `taskset -c 2`), disable turbo for comparisons, and use
  `--benchmark_repetitions=10 --benchmark_report_aggregates_only=true`,
  then compare with `tools/compare.py` from the Google Benchmark
  repository (it reports a U-test p-value).

## Copies, moves, and allocation

- Mistake: `return std::move(local);`. Fix: return the local by name.
  `std::move` disables copy elision (NRVO) and triggers a pessimizing
  move (`-Wpessimizing-move`).
- Mistake: `std::move` on a `const` object, expecting a move. Fix: moving
  a `const T` selects the copy constructor silently; check with
  clang-tidy `performance-move-const-arg` and the assembly.
- Mistake: a move constructor without `noexcept`. Fix: add `noexcept`;
  `std::vector` reallocation uses `std::move_if_noexcept` and copies every
  element when the move can throw.
- Mistake: passing `std::string` by `const&` where the callee only reads.
  Fix: take `std::string_view`, but never store it beyond the owner's
  lifetime, never pass it to a C API needing NUL termination, and never
  build it from a temporary `std::string` that dies at the end of the
  statement.
- Mistake: `find(string_view)` on a `std::string`-keyed map, which builds a
  temporary `std::string` per lookup. Fix: use
  `std::map<std::string, V, std::less<>>` (or transparent hash and
  equality for unordered containers, C++20) so `find(string_view)` does
  not allocate a key.
- Mistake: `vector::push_back` in a loop of known size. Fix: `reserve(n)`
  first. Keep in mind `reserve` past the real need wastes memory and
  `resize` value-initializes every element.
- Mistake: `emplace_back` assumed faster than `push_back`. Fix: they are
  the same for an existing object of the element type; `emplace_back`
  wins only when constructing in place from arguments, and it bypasses
  `explicit` checks.
- Mistake: `std::function` on a hot path. Fix: a template parameter or
  `std::function_ref` (C++26) or a lambda stored by type. `std::function`
  may heap allocate captures and always does an indirect call.
- Mistake: `std::shared_ptr` passed by value through a hot path. Fix: pass
  `const&` or a raw reference when ownership is not shared; every copy is
  an atomic increment and decrement. Prefer `make_shared` (one
  allocation) unless weak pointers outlive the object and memory matters.
- Mistake: small-buffer string assumptions. Fix: SSO capacity differs by
  standard library (15 bytes on libstdc++, 22 on libc++); do not depend
  on it, measure with your target library.

## Containers

- Mistake: `std::map` or `std::list` for a hot lookup. Fix: a sorted
  `std::vector` with `lower_bound`, or a flat hash map, is usually faster
  from locality. Measure with realistic sizes and mutation rates, because
  inserts into a sorted vector are O(n).
- Mistake: `std::unordered_map` with a weak hash (identity hash on
  integers with power-of-two buckets). Fix: a mixing hash, and
  `reserve(n)` to avoid rehashing. Iteration order changes with a new
  hash, so check who depends on it.
- Mistake: keeping iterators, references, or pointers into a vector after
  `reserve` is skipped and a later push reallocates. Fix: keep indexes, or
  reserve once and assert `capacity()` has not changed.
- Mistake: `vector<bool>`. Fix: it is a bit-packed proxy container
  (no `bool&`, slower element access). Use `vector<char>` or
  `vector<uint8_t>` or `std::bitset` when the size is fixed.
- Mistake: `std::sort` on a struct array when the key is one field. Fix:
  sort an index array or key/value pairs only if profiling shows moves
  dominating, and use `std::stable_sort` only when order of equal keys
  matters, since it may allocate.
- Mistake: `std::distance` in a loop on a non-random
  access range. Fix: compute once; `distance` is O(n) there.

## Virtual calls and atomics

- Mistake: removing `virtual` by hand for speed. Fix: mark a class or
  method `final` so the compiler can devirtualize calls through a known
  static type, and check with `-Rpass=devirt` or the assembly; PGO and
  LTO with `-fwhole-program-vtables` (Clang) can devirtualize too.
- Mistake: `std::atomic` with the default `memory_order_seq_cst` assumed
  free. Fix: on x86, stores of seq_cst cost a full fence (`xchg`);
  use `release` stores and `acquire` loads where the protocol allows, and
  justify each relaxed order with the invariant it keeps. Prove it with
  ThreadSanitizer on a stress test, which finds races but not wrong
  orderings.
- Mistake: per-thread counters in one array (false sharing). Fix: pad
  each to `std::hardware_destructive_interference_size` when the library
  defines it, otherwise `alignas(64)`; note that the constant triggers
  `-Winterference-size` in GCC because it is ABI-unstable in headers.
- Mistake: a mutex around a counter or pointer swap measured without
  contention. Fix: benchmark with the real thread count; uncontended
  locks are cheap and contended ones are not, so one thread hides the
  cost.
- Mistake: spin locks without a pause instruction. Fix: use
  `std::this_thread::yield` after a bounded spin or a normal mutex;
  unbounded spinning burns the core that holds the lock when the machine
  is oversubscribed.

## Build and I/O

- Mistake: `-O3 -march=native` shipped to heterogeneous machines. Fix:
  name a baseline ISA level and measure.
- Mistake: `std::endl` per line. Fix: write `'\n'`; `endl` flushes.
  Keep flushes where an interactive consumer needs them.
- Mistake: `std::cin`/`cout` slow and "fixed" by
  `std::ios::sync_with_stdio(false)` alone. Fix: call it before any I/O,
  then never mix with `printf`/`scanf` on the same stream, and untie
  `cin.tie(nullptr)` only if prompts are not relied on. For bulk input,
  read the whole file and parse with `std::from_chars`, which does not
  allocate or use locale.
- Mistake: `std::regex` in a hot path. Fix: it is slow and can overflow
  the stack on long inputs; use a hand parser, RE2, or
  `std::string_view` operations.
- Mistake: LTO/PGO adopted without a dedicated training run or a fresh
  profile after code changed. Fix: regenerate the profile for each
  release, since a stale profile silently mis-optimizes.
