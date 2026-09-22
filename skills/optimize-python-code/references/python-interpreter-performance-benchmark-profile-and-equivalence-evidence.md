# Prove a Python performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Python evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative cProfile for deterministic call accounting, py-spy or another approved sampler, tracemalloc, and native profiling for extensions with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project tests plus iterator-consumption, identity, mutation, exception, ordering, context-manager, and extension-ABI checks; include iterator exhaustion, eager/lazy changes, mutable aliasing, identity-sensitive behavior, exception timing, hash/order assumptions, GIL/threading behavior, and C-extension ownership. | One happy-path output or successful compilation. |
| The operation improved | Matched pyperf or the repository benchmark suite with calibrated loops, process isolation, repeated samples, metadata, and equivalent inputs, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported Python implementations/versions, OS/architecture, wheels and native dependencies, interpreter flags, container limits, serialization behavior, and rollback package. | Success on the author workstation. |

## Verification sequence

1. Record Python implementation/version, optimization/debug build, interpreter
   flags, dependency/extension versions, allocator, operating system, CPU, and
   workload for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
