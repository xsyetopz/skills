---
name: optimize-dotnet-code
description: >-
  Profile or optimize .NET speed, latency, throughput, allocation, and memory
  using runtime, JIT, workload, and native-interop evidence. Not for SDK upgrades.
---

# Optimize .NET Code

Define the workload and limiting metric: startup, throughput, tail latency,
allocation, retained memory, or resource use. Record the selected SDK, target
framework, runtime, architecture, deployment mode and effective build settings.
Preserve those contracts unless changing one is part of the requested
experiment.

Read [measurement and runtime][measurement] for diagnostics, benchmarks and
build evaluation. Read [memory and interop][memory] when the measured path
involves buffers, collection internals, pinning, unsafe code or native
boundaries.

Use profiles to select a concrete path. Remove redundant work before introducing
pooling, unsafe access, new dispatch layers or concurrency. Use maintained BCL
APIs and libraries before writing custom parsers, serializers or native
bindings. Syntax changes, method names and scanner matches are not performance
evidence.

Validate observable behavior before timing: ordering, empty and malformed input,
overflow, culture, cancellation, ownership and concurrent access as applicable.
Measure baseline and candidate under the same workload and settings. Report
variance and allocation tradeoffs; do not extrapolate a microbenchmark into an
application-wide speedup or claim safety from successful compilation.

Use the [runnable comparison benchmark](assets/benchmark-repro/README.md) to
demonstrate correctness-first comparison and local measurement evidence. Do not
transfer its result to another application workload.

[measurement]: references/measurement-and-runtime.md
[memory]: references/memory-and-interop.md
