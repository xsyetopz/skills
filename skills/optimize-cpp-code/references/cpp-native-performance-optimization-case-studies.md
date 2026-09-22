# Optimization case studies for Cpp Native Performance

## Correctness-first hot loop

```cpp
std::size_t count_nonzero(std::span<const std::byte> bytes) {
    return static_cast<std::size_t>(std::ranges::count_if(
        bytes, [](std::byte b) { return b != std::byte{0}; }));
}

// A lower-level loop is not automatically faster. Benchmark the representative
// standard/library/compiler combination and preserve span lifetime and result.
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

- object lifetime, ownership, RAII and move/copy behavior
- iterator/reference/view invalidation and container complexity
- exception guarantees, `noexcept`, error channels and cleanup
- templates, inlining, virtual/type-erased dispatch, ABI and code size
- data races, atomics, locks, memory order and task cancellation
- floating-point rules and undefined behavior
