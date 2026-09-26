# Measurement constructs

Cards for proving a Swift change is equivalent and cheaper: timing
harnesses, allocation and ARC counters, SIL and assembly inspection, and
Instruments. The runnable catalog is
[`assets/examples`](../assets/examples); `verify.sh` copies it to a
temporary directory, so no `.build/` lands in the skill.

Measured on an Apple M1 Max, macOS 27.0 arm64, Apple Swift 6.3.3
selected through `xcrun` (`TOOLCHAINS`), package-benchmark 1.36.2,
xctrace 16.0. Other build jobs shared the machine (load average 9 to
32), so timings are noisy; counts are exact.

## Contents

- ContinuousClock harness
- package-benchmark
- Malloc-zone counting hook
- ARC counting through runtime hooks
- SIL inspection with -emit-sil
- Assembly inspection with -emit-assembly
- xctrace Time Profiler
- xctrace Allocations

## ContinuousClock harness

**Definition.** [`ContinuousClock`][clock] (Swift 5.7, macOS 13) is a
monotonic clock that keeps counting while the system sleeps.
`clock.measure { }` returns the elapsed `Duration` of a closure. The
dependency-free harness below runs warm-up calls, then takes the median
of several samples of many calls each.

**Use when.**

- A pair of functions needs a quick, repeatable comparison and adding a
  package dependency is not acceptable.
- A whole async operation must be timed (`await clock.measure { }`).

**Do not use when.**

- The result must be defended in review or CI: use package-benchmark,
  which adds percentiles, malloc and ARC counters, and baselines.
- The measured closure discards its result: the optimizer can delete
  the work. Pass every result to an opaque sink (`blackHole` below).
- Inputs are built inside the measured closure: their allocations and
  time become part of the result.

**Example.** Runnable: `assets/examples/constructs/Sources/Catalog/`
`Harness.swift`.

```swift
@inline(never)
func blackHole<T>(_ value: T) {
    withUnsafePointer(to: value) { sink &+= Int(bitPattern: $0) & 1 }
}

func medianNanos(samples: Int = 31, calls: Int,
                 _ body: () -> Int) -> Double {
    for _ in 0..<calls { blackHole(body()) }  // warm-up
    let clock = ContinuousClock()
    var results: [Double] = []
    for _ in 0..<samples {
        let d = clock.measure {
            for _ in 0..<calls { blackHole(body()) }
        }
        let c = d.components
        let ns = Double(c.seconds) * 1e9 + Double(c.attoseconds) / 1e9
        results.append(ns / Double(calls))
    }
    results.sort()
    return results[results.count / 2]
}
```

**Cost removed.** Guesswork: a median of 31 samples replaces one
stopwatch reading. Output format:
`TIME reserveCapacity: 4467.9 ns -> 3242.5 ns (median of 31)`.

**Verify.**

1. `sh assets/examples/verify.sh verify` passes first (same results).
1. `sh assets/examples/verify.sh time reserveCapacity` prints one `TIME`
   line per pair; rerun it and treat pairs whose order flips as noise.

## package-benchmark

**Definition.** [package-benchmark][pb] (ordo-one) is a SwiftPM plugin:
executable targets under `Benchmarks/` declare `Benchmark("name") { }`
closures, and `swift package benchmark` runs them in release mode and
prints percentiles per metric. On Swift 6.3+ its malloc statistics come
from the `malloc-interposer` package and need no install; on Swift 6.2
and older they need jemalloc ([Getting started][pb-start]). Metrics
include `.wallClock`, `.mallocCountTotal`, `.retainCount`,
`.releaseCount`, and `.instructions` ([metrics][pb-metrics]).

**Use when.**

- A change needs defensible numbers: p50/p90/p99, malloc counts, and
  retain/release counts per iteration from one tool.
- A baseline must be stored and compared later:
  `swift package --allow-writing-to-package-directory benchmark baseline
  update main`, then `swift package benchmark baseline compare main`
  ([baselines][pb-baseline]).

**Do not use when.**

- The project cannot fetch packages (air-gapped CI): use the
  ContinuousClock harness and the counting hooks in this file.
- You profile the benchmark in Xcode/Instruments: disable the malloc
  backend first (`swift package --disable-default-traits benchmark` or
  `BENCHMARK_DISABLE_MALLOC_INTERPOSER`), as the docs require.

**Example.** Runnable: `assets/examples/benchmarks/` (pinned by
`Package.resolved`).

```swift
import Benchmark
import Constructs

let benchmarks: @Sendable () -> Void = {
    Benchmark.defaultConfiguration.metrics = [
        .wallClock, .mallocCountTotal, .retainCount, .releaseCount,
    ]
    Benchmark("reserveCapacity/baseline") { benchmark in
        for _ in benchmark.scaledIterations {
            blackHole(squaresGrowing(1000))
        }
    }
    Benchmark("reserveCapacity/candidate") { benchmark in
        for _ in benchmark.scaledIterations {
            blackHole(squaresReserved(1000))
        }
    }
}
```

**Cost removed.** Unreported variance and allocation blind spots.
Measured p50 values from `sh verify.sh measure`:

| Pair | Malloc (total) | Retains | Wall clock p50 |
| --- | --- | --- | --- |
| reserveCapacity | 10 -> 1 | 0 -> 0 | 2083 -> 958 ns |
| Dictionary(minimumCapacity:) | 11 -> 1 | 0 -> 0 | 30 -> 14 µs |
| Substring (256 fields) | 267 -> 10 | 513 -> 257 | 123 -> 101 µs |
| linked list vs array | 0 -> 0 | 1001 -> 0 | 14 µs -> 125 ns |

**Verify.**

1. `sh assets/examples/verify.sh verify` (equivalence) before measuring.
1. `sh assets/examples/verify.sh measure`; select with
   `BENCH_FILTER='reserveCapacity.*'`. The `Malloc (total)` and `Retains`
   rows must move in the claimed direction. This machine did not need
   `--disable-sandbox`.

## Malloc-zone counting hook

**Definition.** A test-only C target replaces the allocation function
pointers (`malloc`, `calloc`, `realloc`, `memalign`, and the
`malloc_type_*` variants of zone version 16) of `malloc_zones[0]`, the
default zone returned by [`malloc_get_all_zones`][malloc-h], after making
it writable with `vm_protect`. Each call increments an atomic counter.
`malloc_zone_statistics(NULL, &stats).size_in_use` reports live bytes.

**Use when.**

- An oracle must assert "the candidate allocates less" without a
  package dependency, deterministically, on macOS.
- Retained memory (not allocation count) is the claim: compare
  `size_in_use` before and after keeping a value alive (slice retention).

**Do not use when.**

- Shipping code: the hook rewrites a system structure. Keep it in a test
  or benchmark binary.
- Linux: it has no malloc zone API. Use package-benchmark there.
- Measuring the first call of a function: lazy metadata and caches
  allocate once (a first run counted 71 mallocs where steady state was
  10). The harness runs every body once before counting.
- Restoring read-only protection afterwards: on macOS 27 (xzone malloc)
  that crashed the next allocation with `EXC_BAD_ACCESS`, because the
  page shares mutable allocator state.

**Example.** Runnable: `assets/examples/constructs/Sources/CCount/`
`ccount.c` (excerpt).

```c
int ccount_install_malloc(void) {
    vm_address_t *zones = NULL;
    unsigned count = 0;
    malloc_get_all_zones(mach_task_self(), NULL, &zones, &count);
    malloc_zone_t *z = (malloc_zone_t *)zones[0];
    vm_protect(mach_task_self(), (vm_address_t)z, sizeof(*z), 0,
               VM_PROT_READ | VM_PROT_WRITE);
    om = z->malloc;
    z->malloc = hm;  /* hm: mallocs++; return om(z, size); */
    /* ... calloc, realloc, memalign, malloc_type_* likewise ... */
    return 0;
}
```

**Cost removed.** None by itself: it turns "fewer allocations" into an
assertion. Its counts matched package-benchmark on the same pairs
(`reserveCapacity 10 -> 1`, `Dictionary 11 -> 1`).

**Verify.**

1. `sh assets/examples/verify.sh verify` prints `ALLOC name: a -> b` and
   fails if a pair that claims a reduction does not show one.
1. Cross-check one pair with `sh verify.sh measure`: the
   `Malloc (total)` p50 must equal the hook's count.

## ARC counting through runtime hooks

**Definition.** The Swift runtime calls `swift_retain`/`swift_release`
through the function pointers `_swift_retain`, `_swift_release`,
`_swift_retain_n`, `_swift_release_n`, and `_swift_tryRetain` only after
the flag `_swift_enableSwizzlingOfAllocationAndRefCountingFunctions_`
`forInstrumentsOnly` is set ([HeapObject.cpp][heapobject]). Setting the
flag and wrapping the pointers counts every native retain/release.
package-benchmark uses the same pointers for its `retainCount` metric
(`Sources/SwiftRuntimeHooks/shims.c` in [package-benchmark][pb]).

**Use when.**

- A change claims fewer retains/releases (value types instead of
  classes, `borrowing`, removing linked traversal) and needs a number,
  not a reading of assembly.

**Do not use when.**

- Shipping code: these are private, Instruments-only runtime symbols.
- Objective-C or bridged objects matter: `objc_retain` and
  `swift_unknownObjectRetain` of non-native objects are not counted.
  Read the assembly for those.
- Only the `_swift_retain`/`_swift_release` wrappers are installed:
  array literals use `swift_retain_n`, which then goes uncounted (a
  first test reported 0 retains for `[n, n, n]`).

**Example.** Runnable: `assets/examples/constructs/Sources/CCount/`
`ccount.c` (excerpt).

```c
#define SWIZZLE_FLAG \
    _swift_enableSwizzlingOfAllocationAndRefCountingFunctions_forInstrumentsOnly
extern bool SWIZZLE_FLAG;
extern HeapObject *(*_swift_retain)(HeapObject *);

void ccount_install_arc(void) {
    SWIZZLE_FLAG = true;
    oret = _swift_retain;
    _swift_retain = hret;  /* hret: retains++; return oret(o); */
    /* ... _swift_release, _retain_n, _release_n, _tryRetain ... */
}
```

The flag is a `bool` variable, not a function: calling it crashed with
`EXC_BAD_ACCESS` at the symbol.

**Cost removed.** None by itself. Measured: `RETAIN linked list vs
array: 1002 -> 0`, `RETAIN borrowing init: 8 -> 0`. For the linked-list
pair, package-benchmark's `Retains` p50 is 1001 -> 0, within one retain of
the hook's count.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints `RETAIN name: a -> b`.
1. The same pair under `sh verify.sh measure` shows the `Retains` row
   moving the same way.

## SIL inspection with -emit-sil

**Definition.** `swiftc -emit-sil` prints optimized Swift Intermediate
Language. Dispatch is explicit there: `class_method` is a vtable call,
`witness_method` a protocol-witness call, `objc_method` a message send,
`function_ref` a direct call; `begin_access [dynamic]` is a runtime
exclusivity check. Specialized generic functions carry the mangling
suffix `Tg5`.

**Use when.**

- A card claims devirtualization, specialization, or removed dynamic
  exclusivity checks, and needs proof before timing.
- The question is why WMO or `final` did or did not apply.

**Do not use when.**

- The claim is about machine code (vectorization, bounds checks,
  retain calls after LLVM): read the assembly.
- The product compiles the module differently (single-file versus WMO,
  `-Osize`): inspect with the product's flags, or the answer differs.

**Example.** From `sh assets/examples/verify.sh wmo`:

```sh
# Without WMO: the frontend compiles Use.swift; Counter.swift is only
# parsed, so internal classes are not known to be final.
xcrun swiftc -frontend -emit-sil -O -parse-as-library \
  -module-name WMODemo -sdk "$(xcrun --show-sdk-path)" \
  -primary-file Use.swift Counter.swift -o file.sil
xcrun swiftc -O -wmo -parse-as-library -module-name WMODemo \
  -emit-sil Use.swift Counter.swift -o wmo.sil
grep -c class_method file.sil wmo.sil
```

**Cost removed.** Ambiguity about what the optimizer did. Measured:
`class_method` 2 -> 0 and unspecialized generic references 1 -> 0.

**Verify.**

1. `sh assets/examples/verify.sh wmo` prints both counts and `WMO PASSED`.
1. Repeat with the project's real flags (read them from
   `swift build -c release -v`).

## Assembly inspection with -emit-assembly

**Definition.** `swiftc -O -wmo -emit-assembly` writes the target's
assembly. A function's body starts at its mangled label (for module
`Constructs`, `_` + `$s10Constructs` + length + name) and LLVM ends it
with `; -- End function`. LLVM annotates loop blocks with
`Loop Header` or `in Loop:` comments, so a check can be scoped to the
loop.

**Use when.**

- Confirming a retain (`bl _swift_retain`), indirect call (`blr`),
  message send (`objc_msgSend`), bounds check (`b.ls`/`b.hi` to a `brk`),
  overflow check (`b.vs`), heap box (`swift_allocObject`), or access
  check (`swift_beginAccess`) appears or disappears.

**Do not use when.**

- Asserting on a function the optimizer merged: identical bodies become
  a one-line tail call (`b ...Tm`, "merged"). Assert on the target, or
  make the bodies differ.
- Inspected functions are internal and unused: WMO removes them. Mark
  them `public @inline(never)`.
- The target is not arm64: the patterns (`blr`, `b.vs`) are
  architecture-specific.

**Example.** From `assets/examples/verify.sh`:

```sh
body() {  # body FILE NAME
  awk -v n="$2" '
    BEGIN { pat = "^_\\$s10Constructs" length(n) n "[A-Za-z_].*:$" }
    !on && $1 ~ pat { on = 1 }
    on { print }
    on && /-- End function/ { exit }
  ' "$1"
}
loop() {
  awk '/^L[A-Za-z0-9_]*:/ { in_loop = ($0 ~ /Loop Header|in Loop:/) }
       in_loop { print }'
}
body o.s tallyChecked | loop | grep -cE 'b\.(ls|hs|lo|hi)'
```

**Cost removed.** Timing noise as the only evidence: every `expect` line
in `sh verify.sh asm` is a deterministic check.

**Verify.**

1. `sh assets/examples/verify.sh asm` ends with `ASM PASSED`.
1. If an expected pattern fails on another toolchain, that compiler
   changed the baseline; re-measure before keeping the rewrite.

## xctrace Time Profiler

**Definition.** `xcrun xctrace record --template 'Time Profiler'
--launch -- <binary> <args>` samples call stacks into a `.trace`
bundle; `xcrun xctrace export --input X.trace --xpath
'/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]'`
prints the samples as XML. Requires a full Xcode (xctrace is not in the
Command Line Tools).

**Use when.**

- Attributing CPU time to functions before choosing a card.
- Confirming after a change that the hot frame shrank at the application
  level, not only in a microbenchmark.

**Do not use when.**

- Only Command Line Tools are installed: `xcrun --find xctrace` fails.
- The workload runs for milliseconds: one short run produced zero
  samples for the target function. Profile a run of at least a few
  hundred milliseconds.

**Example.**

```sh
xcrun xctrace record --quiet --template 'Time Profiler' \
  --output time.trace --launch -- .build/release/Catalog time offset
xcrun xctrace export --input time.trace --xpath \
  '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' \
  > profile.xml
grep -c charactersByOffset profile.xml
```

**Cost removed.** Optimizing the wrong function. Rows are deduplicated
references, so count frames with a tool that resolves `ref` attributes
(or open the trace in Instruments) before reporting percentages.

**Verify.**

1. `sh assets/examples/verify.sh trace` prints the matching row count and
   `TRACE PASSED`.

## xctrace Allocations

**Definition.** The `Allocations` template records heap and VM
allocations. Its statistics export through the track detail:
`--xpath '/trace-toc/run[@number="1"]/tracks/track[@name="Allocations"]`
`/details/detail[@name="Statistics"]'`, one row per category with
`count-total`, `total-bytes`, and `persistent-bytes`.

**Use when.**

- Finding which call sites allocate, or measuring persistent (leaked or
  retained) bytes of a whole process run.

**Do not use when.**

- The binary lacks the `com.apple.security.get-task-allow` entitlement:
  the recording reported "Failed to attach to target process",
  never saw the target exit, and ran until `--time-limit` (an earlier
  run without a limit was killed after more than 10 minutes). Sign a
  copy with `codesign -f -s - --entitlements ent.plist` and always pass
  `--time-limit`.
- A per-call count is the claim: use the counting hook or
  package-benchmark, which give exact per-iteration numbers.

**Example.** From `trace` mode in `assets/examples/verify.sh`, after
signing a copy of the binary with the `get-task-allow` entitlement:

```sh
xcrun xctrace record --quiet --template 'Allocations' \
  --time-limit 60s --output alloc.trace --launch -- ./Catalog time lazy
xcrun xctrace export --input alloc.trace --xpath \
  '/trace-toc/run[@number="1"]/tracks/track[@name="Allocations"]'\
'/details/detail[@name="Statistics"]' >alloc.xml
grep 'category="All Heap Allocations"' alloc.xml
```

**Cost removed.** Unattributed allocation volume. Measured:
`count-total="84393"` heap allocations for `Catalog time lazy`.

**Verify.**

1. `sh assets/examples/verify.sh trace` prints `TRACE Allocations:` with
   `count-total` and `total-bytes`.

[clock]: https://developer.apple.com/documentation/swift/continuousclock
[pb]: https://github.com/ordo-one/benchmark
[pb-start]: https://github.com/ordo-one/benchmark/blob/main/Sources/Benchmark/Documentation.docc/GettingStarted.md
[pb-metrics]: https://github.com/ordo-one/benchmark/blob/main/Sources/Benchmark/Documentation.docc/Metrics.md
[pb-baseline]: https://github.com/ordo-one/benchmark/blob/main/Sources/Benchmark/Documentation.docc/CreatingAndComparingBaselines.md
[malloc-h]: https://github.com/apple-oss-distributions/libmalloc/blob/main/include/malloc/malloc.h
[heapobject]: https://github.com/swiftlang/swift/blob/main/stdlib/public/runtime/HeapObject.cpp
