# Optimization case studies for C Native Performance

## Correctness-first hot loop

```c
size_t count_nonzero(const unsigned char *p, size_t n) {
    size_t count = 0;
    for (size_t i = 0; i < n; ++i) count += p[i] != 0;
    return count;
}

/* Optimize only after profiling. A vectorized version must preserve all n,
   unaligned inputs, null policy, and target CPU fallback. */
```

## Matched measurement record

Record at least:

```text
source revision; benchmark case and parameters;
correctness oracle; toolchain and runtime;
build profile, flags, and features; dependencies and lock state;
OS, CPU, and architecture; affinity and power
conditions when material; setup boundary; warmup/forks/repetitions; raw results;
units and variability; profiler evidence; invalid/excluded runs with reasons
```

## Decision example

A candidate reduces a microbenchmark mean by 12% but increases retained memory
4x and does not change application tail latency. Under a latency objective and
memory budget, do not present it as a production improvement. Keep or reject it
using the actual goal and workload.

## Semantic traps to test

- integer width, signed overflow and conversion
- object bounds, alignment, pointer provenance/lifetime, strict aliasing and
  effective type
- allocation ownership, realloc invalidation, cleanup and error paths
- volatile versus atomics, memory order, data races and signal safety
- locale, errno, floating-point environment, I/O buffering and ABI layout
