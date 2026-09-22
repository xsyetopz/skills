# Prove a Kotlin performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Kotlin evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative JFR/async-profiler for JVM, Instruments or platform tools for Native, and browser/runtime tools for JS with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project tests covering nullability, collection strictness/laziness, inline/value behavior, exceptions, structured concurrency, cancellation, and backend parity; include backend conflation, boxing, Sequence evaluation timing, inline/value-class representation, coroutine detachment, dispatcher changes, cancellation, and Java interop. | One happy-path output or successful compilation. |
| The operation improved | Matched a backend-native harness—JMH or kotlinx-benchmark where appropriate—with explicit warmup, setup, state, and result use, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported Kotlin versions and backends, JDK/Native/JS runtime matrix, compiler flags, coroutine library, architecture, binary/metadata compatibility, and rollback artifact. | Success on the author workstation. |

## Verification sequence

1. Record Kotlin/compiler version, JVM/Native/JS backend, target settings,
   dependencies, coroutine dispatcher, runtime flags, architecture, and workload
   for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
