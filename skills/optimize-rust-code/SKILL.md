---
name: optimize-rust-code
description: >-
  Profile or optimize Rust speed, latency, throughput, allocation, binary size,
  and memory using compiler, ownership, concurrency, and CPU evidence. Not for
  toolchain migration.
---

# Optimize Rust Code

Define the workload, build profile, target CPUs, and performance claim. Measure
CPU/allocation behavior before changing the limiting path. Check changes against
the declared MSRV, edition, panic behavior, and overflow semantics.

Read [measurement and build][ref-1] for profiling, Cargo profiles, and PGO. Read
[ownership and concurrency][ref-2] for allocation, layout, unsafe, atomics, and
SIMD.

Remove redundant work and copies before adding unsafe or concurrency complexity.
For unsafe operations, establish caller preconditions, aliasing, alignment,
initialization, bounds, and lifetime. Enforce CPU feature requirements with
runtime dispatch when distributing portable binaries.

Run relevant correctness checks and repeated before/after measurements under
identical build and workload conditions. Report measured scope and variability.
Identify unavailable soundness or target checks without treating compilation as
proof.

Use the [runnable comparison benchmark](assets/benchmark-repro/README.md) when a
controlled same-input comparison is useful. Its checked-in measurement is local
evidence, not a general collection recommendation.

[ref-1]: references/measurement-and-build.md
[ref-2]: references/ownership-and-concurrency.md
