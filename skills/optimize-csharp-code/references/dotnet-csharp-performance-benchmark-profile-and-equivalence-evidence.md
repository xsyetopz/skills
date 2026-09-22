# Prove a C#/.NET performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required C#/.NET evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative dotnet-trace/EventPipe, dotnet-counters, PerfView or platform traces, GC and allocation diagnostics with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project tests plus async/cancellation, pooling ownership, Span/ref lifetime, exception, and interop-lifetime checks; include boxing, hidden allocations, deferred enumeration, ValueTask consumption, pooled-buffer ownership, GC rooting, pinning, delegate lifetime, and async cancellation. | One happy-path output or successful compilation. |
| The operation improved | Matched BenchmarkDotNet with explicit jobs, diagnoses, invocation/setup boundaries, and baseline/candidate identities, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for target frameworks, runtime versions, JIT/AOT modes, GC/container limits, architectures, trimming, interop targets, and rollback package. | Success on the author workstation. |

## Verification sequence

1. Record SDK, target framework, runtime, JIT or Native AOT mode, GC mode,
   evaluated MSBuild properties, ReadyToRun/tiering settings, and architecture
   for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
