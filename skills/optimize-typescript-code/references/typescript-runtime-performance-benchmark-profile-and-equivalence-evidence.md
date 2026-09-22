# Prove a TypeScript performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required TypeScript evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative tsc --extendedDiagnostics or --generateTrace for compiler cost and target-runtime CPU/heap tools for execution cost with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project type checks plus runtime tests for emitted behavior, async completion, rejection, module interop, coercion, and public type/API compatibility; include type erasure, changed compiler target/module output, unsound assertions, different runtime work, premature Promise resolution, module side effects, and runtime-specific optimization. | One happy-path output or successful compilation. |
| The operation improved | Matched the repository runtime harness against the emitted artifact plus compiler diagnostics for type-check/build cost, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported TypeScript/compiler configs, emitted targets/modules, browsers or server runtimes, bundler/minifier settings, declaration/API compatibility, dependency lock, and rollback bundle. | Success on the author workstation. |

## Verification sequence

1. Record TypeScript version, tsconfig inheritance,
   target/module/moduleResolution, emitted/transpiled code, runtime
   engine/version, bundler, dependencies, and workload for baseline and
   candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
