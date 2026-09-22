# Prove a JavaScript performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required JavaScript evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative browser performance/heap tooling or the target server runtime CPU and heap profiler with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | runtime tests covering coercion, property order, prototypes, errors, Promise settlement, cancellation, and resource cleanup; include coercion, sparse arrays, property ordering, prototype accessors, hidden asynchronous work, unhandled rejection, engine-specific optimization, and changed module loading. | One happy-path output or successful compilation. |
| The operation improved | Matched the repository harness in the target engine with warmup, equivalent asynchronous completion, repeated samples, and consumed results, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported browsers or server runtimes, engine versions, CPU/OS targets, module/bundler output, feature detection, dependency lock, and rollback bundle. | Success on the author workstation. |

## Verification sequence

1. Record actual browser or server engine, version, flags, module system,
   event-loop conditions, dependency graph, hardware, and workload for baseline
   and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
