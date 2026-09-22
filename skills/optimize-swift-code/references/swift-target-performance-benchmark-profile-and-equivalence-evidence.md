# Prove a Swift performance claim

Use evidence at the same boundary as the claim. A build proves that code was
accepted by one toolchain. A unit test proves only the exercised behavior. A
microbenchmark proves only the measured operation and environment.

| Claim | Required Swift evidence | Invalid substitute |
| --- | --- | --- |
| The target is a hotspot | Representative Instruments Time Profiler, Allocations, Leaks, Points of Interest, and target-specific signposts with source/symbol attribution and cost share. | Source inspection or intuition. |
| Behavior is preserved | project tests covering value/reference semantics, copy-on-write sharing, ownership, exclusivity, Unicode indices, errors, Sendable, and actor isolation; include copy-on-write uniqueness, ARC traffic and lifetime, exclusivity, bridging, String indices/Unicode, unsafe buffers, error timing, Sendable conformance, and actor isolation. | One happy-path output or successful compilation. |
| The operation improved | Matched XCTest performance metrics, Swift Benchmark, or the repository harness with controlled setup, repeated measures, and consumed outputs, repeated observations, units, variance/distribution, and validated outputs. | One stopwatch sample or different build settings. |
| Memory improved | Allocation and retained/live-memory evidence for the same workload. | Fewer allocation expressions in source. |
| Application objective improved | End-to-end latency, throughput, CPU, or memory at the requested boundary. | Microbenchmark result only. |
| Fleet is safe | Tests for supported Apple/non-Apple platforms, SDK and deployment targets, Swift runtime compatibility, architectures, optimization mode, package graph, signing, and rollback artifact. | Success on the author workstation. |

## Verification sequence

1. Record Swift/Xcode toolchain, SDK and deployment target, optimization and
   whole-module settings, architecture, dependencies, ARC behavior, and workload
   for baseline and candidate.
1. Run the same independent semantic/safety checks on both revisions.
1. Collect a baseline profile and matched repeated benchmark.
1. Apply one hypothesis-sized change.
1. Repeat the same profile. Verify that the predicted cost declines rather than
   moving into an unmeasured child, allocator, kernel, or asynchronous task.
1. Repeat the matched benchmark and the application-level workload.
1. Report raw artifacts, exclusions, failed runs, tradeoffs, and unmeasured
   targets. Do not convert an unexecuted command into a passed check.
