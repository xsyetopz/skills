---
name: optimize-rust-code
description: >-
  Use only when explicitly invoked by name. Profile, review, or optimize Rust
  performance using allocation, layout, ownership, concurrency, and compiler
  evidence. Includes unsafe and CPU-portability tradeoffs; excludes unrelated
  toolchain migration.
---

# Optimize Rust Code

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

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

[ref-1]: references/measurement-and-build.md
[ref-2]: references/ownership-and-concurrency.md
