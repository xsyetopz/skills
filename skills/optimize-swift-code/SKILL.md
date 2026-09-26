---
name: optimize-swift-code
description: >-
  Profiles and optimizes Swift CPU time, allocations, and ARC traffic with
  package-benchmark, Instruments, and SIL or assembly. Use when a Swift
  benchmark or profile shows the cost. Not for deployment-target bumps.
---

# Optimize Swift Code

Make a measured Swift hot path cheaper without changing observable
behavior. Each change applies one reference card to a cost that a profile
attributes, is proven equivalent by an oracle, and is kept only if the
metric the card names improves: malloc calls, retains, hash calls, an
instruction pattern in SIL or assembly, or a benchmark percentile. Several
cards record classic rewrites that measured as **no difference** because
`-O` with whole-module optimization already did the work, so check the
real build before rewriting.

## Workflow

1. Record the target: `xcrun swift --version`, `Package.swift` platforms
   and `swiftLanguageModes`, and the flags the release build really
   passes (`xcrun swift build -c release -v`: look for `-O`,
   `-whole-module-optimization`, `-enable-default-cmo`,
   `-enable-library-evolution`). Keep the toolchain, deployment target,
   and flags unless the task is the build configuration.
1. Reproduce the workload in a release build (`swift build -c release`,
   or Xcode's Release configuration). Pick the metric the user cares
   about: time per operation, wall time, allocations, retains, peak or
   retained memory, or binary size.
1. Attribute the cost before editing
   ([measurement](references/measurement.md)):
   - CPU: `xcrun xctrace record --template 'Time Profiler' --launch --`
     on the release binary (needs full Xcode).
   - Allocations and ARC: package-benchmark with `.mallocCountTotal`,
     `.retainCount`, `.releaseCount`, or the counting hooks in
     `assets/examples/constructs/Sources/CCount`.
   - One function: read its assembly (`-emit-assembly`) or SIL
     (`-emit-sil`) for `blr`, `objc_msgSend`, `swift_retain`,
     `swift_allocObject`, `swift_beginAccess`, `b.vs`, or bounds traps.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty, one element, boundary sizes, non-ASCII and grapheme
   clusters (combining marks, ZWJ emoji, flags, `\r\n`), overflow, and
   error paths. `Sources/Catalog/Checks.swift` shows the shape.
1. Apply the change. Put a `// PERF/SAFETY:` comment on every
   `withUnsafe...` closure, `unsafe` expression, unchecked subscript, and
   memory ordering weaker than sequentially consistent, stating the proof.
1. Verify with the card's **Verify** steps: behavior first, then the
   named metric. Count allocations and retains on a second, warmed-up run;
   the first run includes one-time metadata allocations.
1. Measure baseline and candidate with the same toolchain, flags, input,
   and machine (package-benchmark baselines, or the ContinuousClock
   harness). Keep the change only if the metric moves beyond run-to-run
   noise and the application workload improves too.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| Measurements from a debug build | [-O release](references/build-settings.md#release-builds-with--o) |
| Binary size is the goal | [-Osize](references/build-settings.md#-osize) |
| Someone proposes `-Ounchecked` | [-Ounchecked](references/build-settings.md#-ounchecked), [wrapping](references/memory.md#wrapping-arithmetic) |
| `class_method` or generic calls across files, custom build | [WMO](references/build-settings.md#whole-module-optimization) |
| Calls into another module's small functions | [CMO](references/build-settings.md#cross-module-optimization-and-library-evolution), [@inlinable](references/dispatch.md#inlinable-usablefrominline-and-frozen-across-modules) |
| `swift_beginAccess` in a profile | [local accumulator](references/memory.md#local-accumulator-instead-of-a-class-property), [flag](references/build-settings.md#-enforce-exclusivityunchecked) |
| `blr` vtable calls on a leaf class | [final](references/dispatch.md#final-classes-and-members), [access control](references/dispatch.md#access-control-that-lets-wmo-infer-final) |
| `objc_msgSend` from Swift callers | [@objc dynamic](references/dispatch.md#avoiding-objc-dynamic) |
| Witness calls through `any P` | [some P](references/dispatch.md#generic-specialization-instead-of-any-p-parameters), [stored generic](references/dispatch.md#generic-stored-property-instead-of-a-stored-existential), [enum](references/dispatch.md#enum-instead-of-an-array-of-existentials) |
| `AnyObject` protocol suggested for ARC | [class-constrained](references/dispatch.md#class-constrained-protocols) |
| One allocation per element of plain data | [struct](references/memory.md#structs-instead-of-classes-for-plain-data) |
| Retains proportional to a traversal | [contiguous values](references/memory.md#contiguous-values-instead-of-linked-nodes) |
| Struct with class storage copies or aliases | [COW](references/memory.md#copy-on-write-with-isknownuniquelyreferenced) |
| `x = f(x)` copies a collection | [inout](references/memory.md#inout-instead-of-copy-and-reassign), [consuming](references/memory.md#consuming-parameters), [consume](references/memory.md#the-consume-operator) |
| Retain per initializer call | [borrowing](references/memory.md#borrowing-parameters) |
| Class that only owns a resource | [~Copyable](references/memory.md#noncopyable-types) |
| `swift_allocObject` for a captured `var` | [inout](references/memory.md#inout-instead-of-a-captured-var) |
| `b.vs` overflow branches block vectorization | [wrapping](references/memory.md#wrapping-arithmetic) |
| Array growth reallocations | [reserveCapacity](references/collections.md#array-reservecapacity), [reduce(into:)](references/collections.md#reduceinto-instead-of-reduce-with-array-concatenation) |
| `_CocoaArrayWrapper` in a class-array loop | [ContiguousArray](references/collections.md#contiguousarray-for-class-elements) |
| Bounds trap in a loop | [monotonic](references/collections.md#withunsafebufferpointer-on-a-monotonic-loop), [data-dependent](references/collections.md#withunsafemutablebufferpointer-for-data-dependent-indices) |
| Generic `Sequence` API is hot | [contiguous storage](references/collections.md#withcontiguousstorageifavailable-fast-path), [Span](references/collections.md#span-parameters) |
| Byte-by-byte integer decoding | [RawSpan](references/collections.md#rawspan-loads) |
| Dictionary rehashing or double lookups | [minimumCapacity](references/collections.md#dictionary-minimumcapacity), [default subscript](references/collections.md#dictionary-subscript-with-default) |
| Intermediate arrays in `map`/`filter` chains | [lazy](references/collections.md#lazy-sequences) |
| Memory retained by small slices | [copy slice](references/collections.md#copy-a-slice-at-an-ownership-boundary) |
| `removeFirst` in a drain loop | [popFirst](references/collections.md#queue-with-popfirst-instead-of-removefirst) |
| Grapheme iteration for byte scans | [utf8 view](references/strings.md#utf-8-view-instead-of-character-iteration) |
| `String(substring)` per field | [Substring](references/strings.md#substring-instead-of-string-copies), [small strings](references/strings.md#small-strings) |
| `index(_:offsetBy:)` in a loop | [iterate](references/strings.md#iteration-instead-of-index-offsetby) |
| String `+=` reallocations | [reserveCapacity](references/strings.md#string-reservecapacity) |
| Shared mutable state across tasks | [actor](references/concurrency.md#actor-isolated-state), [Mutex](references/concurrency.md#mutex-from-synchronization), [Atomic](references/concurrency.md#atomic-from-synchronization), [unfair lock](references/concurrency.md#osallocatedunfairlock) |
| `await actor.method()` per element | [batching](references/concurrency.md#batching-actor-calls) |
| One busy core on independent CPU work | [TaskGroup](references/concurrency.md#taskgroup-for-cpu-bound-work) |

## Rules

- Release builds only, same flags for baseline and candidate. A debug
  build has different ARC, inlining, and specialization.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric does not move; several cards record exactly
  that outcome.
- A candidate that does less work is invalid: skipped validation, a
  smaller input, a cached result, a dropped overflow check, a byte scan
  replacing a grapheme-correct scan, or an unordered result replacing an
  ordered one.
- Preserve value semantics (a shared copy must not see a mutation),
  identity (`===`), `deinit` timing, error and trap behavior, Unicode
  semantics, actor isolation, and `Sendable` guarantees.
- Unsafe pointers, unchecked subscripts, `-Ounchecked`, and
  `-enforce-exclusivity=unchecked` need a written proof and the assembly
  showing the safe form still pays the check. Never ship the counting
  hooks: they use private runtime and allocator symbols.
- `@inlinable`, `@frozen`, and `final` on public API are ABI and
  source-compatibility promises; do not add them to a library without
  its owner's approval.
- Only numbers you measured (state machine, toolchain, load) or numbers
  from a linked primary source go in the report. Timings from a shared
  machine are labeled as such.

## Bundled tools

`assets/examples/verify.sh` copies the catalog to a temporary directory
and runs everything through `xcrun`:

- `verify` (default): oracles plus malloc, retain, hash-call, and
  `next()`-call assertions for every pair.
- `benchmark`: runs every pair once; smoke only, no timing.
- `asm`: emits assembly with `-O`, library evolution,
  `-Ounchecked`, and `-enforce-exclusivity=unchecked`, and asserts
  dispatch, ARC, bounds, overflow, and access-check patterns (arm64).
- `wmo`: SIL with and without whole-module optimization.
- `build`: `-O` versus `-Osize` sizes and the `-O` overflow trap.
- `time [filter]`: ContinuousClock medians per pair.
- `measure`: package-benchmark pinned by `benchmarks/Package.resolved`
  (`BENCH_FILTER` selects).
- `trace`: xctrace Time Profiler and Allocations recordings.

## References

- [Measurement](references/measurement.md): ContinuousClock,
  package-benchmark, malloc and ARC hooks, SIL, assembly, xctrace.
- [Build settings](references/build-settings.md): `-O`, `-Osize`,
  `-Ounchecked`, WMO, CMO and library evolution, exclusivity flag.
- [Dispatch](references/dispatch.md): final, access control, `@objc
  dynamic`, generics versus existentials, `@inlinable`.
- [Values, ARC, and ownership](references/memory.md): structs, COW,
  `inout`, `consuming`, `borrowing`, `~Copyable`, exclusivity, captures,
  wrapping arithmetic.
- [Collections](references/collections.md): capacity, `ContiguousArray`,
  unsafe buffers, `Span`, `RawSpan`, dictionaries, `lazy`, slices.
- [Strings](references/strings.md): UTF-8 view, `Substring`, indexing,
  capacity, small strings.
- [Concurrency](references/concurrency.md): actors, `Mutex`, `Atomic`,
  `OSAllocatedUnfairLock`, batching, `TaskGroup`.

## Completion evidence

The final report contains:

- `swift --version`, deployment target, OS and CPU, and the release
  flags from `swift build -c release -v`;
- the profile, counter, or assembly evidence that attributed the cost;
- the card applied, its preconditions checked, and its counter-indications
  ruled out;
- the oracle command and result, including Unicode, empty, boundary, and
  overflow cases;
- baseline and candidate numbers from the same build and machine, with
  units, percentiles or spread, and machine load, plus the
  application-level result;
- every check not run (Linux, other architectures, Instruments without
  full Xcode, older deployment targets) stated as not verified.
