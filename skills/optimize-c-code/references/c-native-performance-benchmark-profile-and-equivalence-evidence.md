# Prove a C performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required C evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative perf or the platform profiler, compiler optimization records, and hardware counters with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | unit/differential tests plus AddressSanitizer, UndefinedBehaviorSanitizer, and ThreadSanitizer where supported; include strict aliasing, signed overflow, object lifetime, alignment, bounds, integer width, data races, and ABI layout. | One happy-path output or successful compilation. |
| The operation improved | Matched the repository benchmark or a process-level runner such as hyperfine with identical executables and inputs, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported compilers, CPU feature baseline, libc/allocator, operating systems, shared-library ABI, and fallback path. | Success on the author workstation. |

## Verification sequence

1. Record compiler version, C standard, target ISA, optimization flags, linker,
   libc, allocator, and ABI for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
