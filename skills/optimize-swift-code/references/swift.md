# Profile and optimize Swift programming-language code

Record Swift/compiler version, target OS and architecture, optimization mode,
whole-module/library-evolution settings, and framework versions. Compare
optimized builds on deployment-representative hardware; simulator and device
performance are not interchangeable.

Use Instruments or the project's platform-appropriate profiler to distinguish
CPU, allocations, retain/release traffic, contention, and UI scheduling.
Establish a representative interaction or workload before changing
value/reference representation.

Inspect copy-on-write behavior and uniqueness at the actual mutation site. A
struct can contain reference-backed storage, and a value-type rewrite can
increase copying. Slices can retain larger backing storage. Generic
specialization, existential containers, bridging to Objective-C, and ARC costs
depend on the concrete call path and optimization visibility.

Use scoped unsafe buffer APIs when a measured hot path needs direct storage
access. Do not let a pointer escape its valid scope, mutate overlapping storage
unsafely, or confuse initialized capacity with element count. `withUnsafe...`
naming does not remove the caller's lifetime obligations.

Preserve actor isolation, cancellation, and task ownership when changing
concurrency. Moving work off the main actor is not sufficient if results later
apply to stale state. Batching actor hops can help a measured path but must
preserve ordering and responsiveness.

Validate error paths, large data, and concurrent ownership separately from
timing. A faster isolated function that stalls the UI or increases memory
retention can be a regression for the user's actual goal.

Sources: [Swift optimization tips][swift-optimization-tips], [Swift
concurrency][swift-concurrency], [Swift memory safety][swift-memory-safety].

## Executable fixtures

Requires Swift 6 toolchain and POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in
[the swift assets](../assets/examples). Copy that directory intact when adapting
a fixture. Run only this language; the target project keeps its own toolchain.

### Semantic regression cases

Source: [Semantics.swift][ref-semantics-swift].

| Case | Required contract |
| --- | --- |
| 1 | ArraySlice indices are not rebased |
| 2 | Extended grapheme clusters versus UTF-8 bytes |
| 3 | Class alias versus independent snapshot |
| 4 | Reporting integer overflow |
| 5 | Duplicate preservation |
| 6 | Zero versus missing optional value |
| 7 | Deterministic child cancellation propagation |
| 8 | Sequential idempotent completion (not a thread-safety proof) |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The
[shared contract](swift-target-performance-executable-performance-fixtures.md)
explains input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Work in a copy of [the swift asset directory](../assets/examples). Run the
following commands relative to that copied directory.

Use the project's existing Swift Benchmark target; do not turn the comparison
CLI into a home-made timing library. The bundled comparison programs test
equivalence and expose callable functions, not speedup claims. Run
`sh verify.sh comparisons` from its root first.

Use the same release build, optimization and whole-module settings. Keep ARC
traffic, copies and task completion inside the boundary when callers pay them.
Await async work; a Task creation benchmark is not a completed-operation
benchmark. Distinguish Darwin and Linux evidence.

Integrate the selected baseline and candidate functions into the native
benchmark framework already used by the target repository. Record its exact
version and configuration; retain its result format, warmups/forks, parameters
and native controls. Test an independent expected result before measurement.
Keep one source of benchmark configuration instead of a separate skill_config
file. Declare any new package installation before performing it. Provision the
target benchmark dependencies explicitly; the example alone does not demonstrate
a performance gain.

Source: [source][source]

## Failure reproduction

Source: [the isolated reproducer][ref-the-isolated-reproducer]. From the skill
root, run `sh assets/examples/verify.sh reproduction`. Direct commands below
assume a clean copy of the reproduction directory.

Expected: a queue result has zero-based indices and independent storage.

Actual: slicing preserves the original start index (`2`) and can retain the
owner's storage. The verifier copies, compiles, and runs `Repro.swift` in a
temporary directory. Exit zero reproduces the documented index behavior.

[swift-optimization-tips]:
  https://github.com/swiftlang/swift/blob/main/docs/OptimizationTips.rst
[swift-concurrency]:
  https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/
[swift-memory-safety]:
  https://docs.swift.org/swift-book/documentation/the-swift-programming-language/memorysafety/
[source]: https://github.com/ordo-one/package-benchmark
[ref-the-fixture-execution-contract]:
  swift-target-performance-executable-performance-fixtures.md
[ref-semantics-swift]: ../assets/examples/correctness/Semantics.swift
[ref-the-isolated-reproducer]: ../assets/examples/reproduction
