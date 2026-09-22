# Optimization case studies for Go Runtime Performance

## Correctness-first hot loop

```go
func countNonZero(data []byte) int {
    count := 0
    for _, b := range data {
        if b != 0 { count++ }
    }
    return count
}

// Parallelizing this loop may be slower and changes scheduling or ownership.
// Profile
// representative sizes before adding goroutines.
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

- slice/map/string aliasing and backing-array retention
- interface boxing/dynamic dispatch and escape to heap
- goroutine ownership, cancellation, channel closure and leaks
- sync/atomic/locks/memory model and data races
- error identity/wrapping, defer/recover and cleanup
- map iteration order, Unicode/rune versus byte behavior
