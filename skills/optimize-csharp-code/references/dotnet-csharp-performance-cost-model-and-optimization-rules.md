# C#/.NET cost model and optimization decisions

An optimization decision connects a measured dominant cost to one change that is
expected to reduce that cost. Use this path only when a representative profile
or counter identifies material cost. Do not use it for style cleanup, unmeasured
folklore, or a candidate that changes the required work.

## Select the next experiment

| Observation | Candidate class | Preserve | Reject when |
| --- | --- | --- | --- |
| Algorithmic growth dominates | Reduce operations or choose a better algorithm/data structure. | Output, errors, ordering, and input domain. | The benchmark uses a smaller or precomputed input. |
| Allocation or retention dominates | Reuse, stream, reserve, compact, or change representation. | Ownership, lifetime, aliasing, and memory ceiling. | Retained memory, copying, or caller mutation increases outside the goal. |
| CPU samples concentrate in one operation | Reduce calls, data movement, dispatch, bounds work, or conversions. | boxing, hidden allocations, deferred enumeration, ValueTask consumption, pooled-buffer ownership, GC rooting, pinning, delegate lifetime, and async cancellation. | The candidate relies on undefined, target-only, or unverified behavior. |
| Contention or scheduling dominates | Shorten critical sections, partition state, batch work, or remove shared work. | Ordering, cancellation, fairness, progress, and errors. | Throughput rises by dropping work or violating synchronization. |
| I/O or syscall wait dominates | Batch, buffer, pipeline, or remove redundant round trips. | Durability, timeout, backpressure, framing, and partial-failure behavior. | A cache or mock hides the production boundary. |

Record SDK, target framework, runtime, JIT or Native AOT mode, GC mode,
evaluated MSBuild properties, ReadyToRun/tiering settings, and architecture.
Measure with BenchmarkDotNet with explicit jobs, diagnoses, invocation/setup
boundaries, and baseline/candidate identities. The cost removed is the profile
share, allocation/retention count, synchronization delay, or I/O operations that
the hypothesis names. Verify the removal by repeating the same profile or
counter and then the same end-to-end metric. A faster microbenchmark without the
predicted cost change does not confirm the hypothesis.

## Required stop conditions

- Stop when baseline and candidate use different inputs, build/runtime settings,
  setup boundaries, or output checks.
- Stop when equivalence for boxing, hidden allocations, deferred enumeration,
  ValueTask consumption, pooled-buffer ownership, GC rooting, pinning, delegate
  lifetime, and async cancellation cannot be tested.
- Do not use a language/runtime upgrade, unsupported CPU feature, unsafe code,
  or public-contract change unless the request authorizes that separate choice.
