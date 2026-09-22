# Prove a Java/JVM performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Java/JVM evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative Java Flight Recorder, JFR event analysis, GC logs, async-profiler or approved platform profiler, and JIT compilation data with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project tests plus concurrency happens-before, ordering, exceptions, serialization, and allocation/lifetime checks; include dead-code elimination, constant folding, shared JMH state, insufficient warmup, boxing, allocation, class initialization, safepoints, synchronization, and memory visibility. | One happy-path output or successful compilation. |
| The operation improved | Matched JMH with explicit forks, warmup/measurement iterations, state scope, parameters, and a consumed result, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported JDKs, JVM flags, GC, heap/container limits, CPU architecture, classpath/module settings, serialization contracts, and rollback artifact. | Success on the author workstation. |

## Verification sequence

1. Record JDK build, JVM flags, GC, heap/container limits, classpath, JIT
   tiering, warmup phase, architecture, and dependency graph for baseline and
   candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
