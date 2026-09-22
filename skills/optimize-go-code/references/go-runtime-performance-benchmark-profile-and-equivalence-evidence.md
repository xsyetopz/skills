# Prove a Go performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Go evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative pprof CPU/heap/block/mutex profiles, execution traces, and compiler escape-analysis diagnostics with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | go test, race detector, fuzz/property or differential checks, goroutine-leak checks, and cancellation tests; include slice and map aliasing, retained backing arrays, escape-to-heap changes, goroutine leaks, cancellation, channel closure, scheduler contention, and data races. | One happy-path output or successful compilation. |
| The operation improved | Matched testing.B benchmarks with setup outside timed work, ReportAllocs, repeated counts, and benchstat comparison, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for Go versions, GOOS/GOARCH, CPU baseline, build tags, GOMAXPROCS/GC policy, cgo dependencies, container limits, and rollback binary. | Success on the author workstation. |

## Verification sequence

1. Record Go version, GOOS/GOARCH, build tags, compiler flags, GOMAXPROCS, GC
   settings, CPU topology, and module graph for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
