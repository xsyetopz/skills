# Swift Performance Gotchas

Benchmark with `package-benchmark` (ordo-one), profile with Instruments (Time Profiler, Allocations)
or `perf` on Linux, and inspect what the compiler did with `swiftc -O -emit-sil` or
`-emit-assembly`. Measure release builds only: `swift build -c release` or `swift test -c release`.
Debug builds keep retain/release traffic and generics unspecialized.

## Contents

- [Measurement](#measurement)
- [ARC and Memory](#arc-and-memory)
- [Dispatch and Generics](#dispatch-and-generics)
- [Strings and Collections](#strings-and-collections)
- [Concurrency](#concurrency)

## Measurement

- Mistake: benchmarking a debug build, or `measure {}` in XCTest on a debug scheme. Fix: release
  configuration, and record the toolchain (`swift --version`) and the platform; optimizer behavior
  changes between releases.
- Mistake: a benchmark body whose result is unused. Fix: call `blackHole(x)` (package-benchmark) on
  the result; the optimizer removes pure work.
- Mistake: reading wall time alone. Fix: package-benchmark reports malloc counts, retains and
  releases, and peak memory; ARC traffic often explains the time, and counts are more stable than
  timings.
- Mistake: comparing with a stale baseline. Fix: use `swift package benchmark baseline update` and
  `baseline compare` so both sides come from the same machine and run.

## ARC and Memory

- Mistake: assuming a class is slow because it allocates. Fix: look for retain/release pairs in
  Instruments or `-emit-sil` around loops; passing class references through generic or escaping
  boundaries adds them. Convert hot small types to `struct` only if identity and shared mutation are
  not part of the contract.
- Mistake: copying large value types with copy-on-write storage and mutating inside a loop. Fix:
  check uniqueness: a second reference to the same `Array` makes the first mutation copy the whole
  buffer. Mutate through `inout` or a local `var`, and avoid storing another copy of the array while
  you mutate.
- Mistake: `array.append` in a loop of known size. Fix: `reserveCapacity(n)` first;
  `Array(unsafeUninitializedCapacity:)` for the fastest fill, with an exact initializedCount on all
  paths, including thrown errors.
- Mistake: `array[i...j]` slices kept around. Fix: an `ArraySlice` keeps the whole base buffer
  alive; copy with `Array(slice)` when it outlives the source. Indexes of a slice start at
  `startIndex`, not 0.
- Mistake: closures capturing `self` in hot paths, or escaping closures per call. Fix: escaping
  closures allocate a context; make parameters non-escaping where possible, and use `[weak self]`
  only when needed since weak references cost extra side-table allocations and atomic operations.
- Mistake: `unowned(unsafe)` or `Unmanaged` to cut ARC. Fix: only after a profile shows
  retain/release dominates and the lifetime is proven; use-after-free is the failure mode. Prefer
  `borrowing`/`consuming` parameter modifiers (Swift 5.9+) and `~Copyable` types to remove copies
  safely.
- Mistake: `[String: Any]`, `Any`, and existential `protocol` values in hot paths. Fix: generics
  constrained by the protocol (specialized at compile time) or `some P`; `any P` uses a boxed
  existential with dynamic dispatch, and values over three words allocate.

## Dispatch and Generics

- Mistake: generic functions across module boundaries assumed specialized. Fix: the optimizer
  specializes only what it can see. Mark hot generics `@inlinable` (and `@usableFromInline` for what
  they touch) or enable cross-module optimization (`-cross-module-optimization`, on by default for
  SwiftPM release builds in recent toolchains; check your version). `@inlinable` makes the body part
  of the module's ABI and source compatibility, so it is a public commitment.
- Mistake: protocols and classes called through dynamic dispatch. Fix: mark classes `final`, members
  `private` or `fileprivate`, and enable whole-module optimization (`-wmo`, the default in release
  builds) so the compiler devirtualizes. Avoid `@objc dynamic` on hot members, which forces
  `objc_msgSend`.
- Mistake: `@inline(__always)` on large functions. Fix: it increases code size; use it on tiny leaf
  functions only, after checking SIL.
- Mistake: `@_specialize` or `@_optimize` hints as a first step. Fix: underscored attributes are
  unsupported and change; prefer `final`, `@inlinable`, and concrete types.
- Mistake: integer arithmetic that overflows to trap checks in the hot loop. Fix: use `&+`, `&*`
  (wrapping) only where wraparound is the intended semantics; `-Ounchecked` removes overflow and
  bounds checks and turns bugs into undefined behavior, so it needs an explicit decision.

## Strings and Collections

- Mistake: `String.count`, `string[index]` via repeated `index(_:offsetBy:)`, or `Character`
  iteration in a parser. Fix: `String` is a Unicode-correct collection, so `count` is O(n) and
  integer subscripting does not exist. Parse over `string.utf8` (or
  `withContiguousStorageIfAvailable`) when the format is ASCII or byte-delimited, and keep
  `Character` semantics only where grapheme clusters are part of the contract.
- Mistake: `Substring` stored long term. Fix: it retains the parent string; convert with
  `String(sub)` when it outlives the source.
- Mistake: string `+=` or interpolation in loops. Fix: reserve capacity (`reserveCapacity`) and
  append; small strings up to 15 UTF-8 bytes are stored inline on 64-bit, so they do not allocate.
- Mistake: `components(separatedBy:)`, `NSString` bridging, or `Regex` per record. Fix:
  `split(separator:)` over `utf8` or a `Substring` scan; Foundation calls bridge and allocate,
  especially on Darwin.
- Mistake: `Dictionary`/`Set` keyed by a custom struct with a synthesized `Hashable` of many fields.
  Fix: hash only the fields that define identity (`hash(into:)` and `==` must agree). Reserve
  capacity with `Dictionary(minimumCapacity:)`. Note that Swift's hashing is seeded per process, so
  iteration order changes between runs; sort when the output order is observable.
- Mistake: `array.contains` in a loop or `filter(...).first`. Fix: a `Set`, or `first(where:)`,
  which stops early; `lazy` chains re-run on every access.
- Mistake: `ContiguousArray` assumed universally better. Fix: it saves bridging cost only for class
  element types and Objective-C interop on Darwin; on Linux `Array` and `ContiguousArray` behave the
  same.

## Concurrency

- Mistake: `DispatchQueue.sync` inside hot paths or a global serial queue as a lock. Fix: use
  `OSAllocatedUnfairLock` or `Mutex` (Swift 6 `Synchronization`, availability per platform), and
  keep critical sections small; never block the main actor.
- Mistake: an `actor` hop per small operation. Fix: each cross-actor call suspends and resumes;
  batch work into one isolated method, or use a nonisolated pure function for computation. Mind
  reentrancy: state can change across an `await`.
- Mistake: `Task {}` per element. Fix: a `TaskGroup` with bounded concurrency (add a new child only
  after one finishes); creating a task allocates and schedules, so unstructured tasks in a loop can
  exhaust the cooperative pool, which is sized to the core count.
- Mistake: blocking the cooperative thread pool with `semaphore.wait()` or `sleep` inside async
  code. Fix: `Task.sleep` and async APIs; blocked pool threads can deadlock the runtime.
- Mistake: `@unchecked Sendable` or `nonisolated(unsafe)` added to silence diagnostics while
  optimizing. Fix: fix the ownership model instead; data races are undefined behavior.
