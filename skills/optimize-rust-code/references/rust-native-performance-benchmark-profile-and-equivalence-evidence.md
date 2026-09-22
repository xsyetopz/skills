# Prove a Rust performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Rust evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative perf, samply, Instruments or the target profiler plus compiler/LLVM diagnostics when they answer the hypothesis with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | cargo test plus Miri, sanitizers, Loom, fuzz/property, or differential checks where the changed unsafe/concurrency boundary requires them; include unsafe invariants, aliasing, provenance, drop order, ownership transfer, panic behavior, integer overflow mode, atomics, target features, and monomorphization/code size. | One happy-path output or successful compilation. |
| The operation improved | Matched Criterion or the repository cargo benchmark with matched profiles/features, warmup/samples, stable inputs, and black-boxed outputs, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for MSRV/toolchain, target triples, CPU feature baseline, features, allocator, panic/LTO profile, C ABI dependencies, architecture, and rollback binary. | Success on the author workstation. |

## Verification sequence

1. Record Rust toolchain, target triple and CPU features, Cargo profile,
   LTO/codegen units, panic mode, features, allocator, dependencies, and
   workload for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
