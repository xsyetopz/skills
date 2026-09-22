# Prove a Scala performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Scala evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative JFR/async-profiler for JVM and the declared runtime profiler for Scala.js or Native with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project tests covering collection strictness/laziness, ordering, effects, exceptions, Futures/execution contexts, boxing, and backend behavior; include backend conflation, strict/lazy collection changes, iterator reuse, boxing/specialization, implicit conversions, initialization, Future scheduling, effects, and exception timing. | One happy-path output or successful compilation. |
| The operation improved | Matched JMH for Scala/JVM or the backend-native repository harness with explicit warmup, forks, setup, state, and consumed results, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported Scala versions/backends, JDK/runtime matrix, compiler flags, binary compatibility, GC/container settings, dependencies, architecture, and rollback artifact. | Success on the author workstation. |

## Verification sequence

1. Record Scala/compiler version, JVM/JS/Native backend, JDK/runtime flags, GC,
   dependencies, build settings, architecture, and workload for baseline and
   candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
