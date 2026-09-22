# Optimization case studies for Swift Target Performance

## Correctness-first hot loop

```swift
func countNonZero(_ bytes: [UInt8]) -> Int {
    var count = 0
    for value in bytes where value != 0 { count += 1 }
    return count
}

// Avoid converting Data, Array, or String for a “faster” loop unless
// ownership,
// CoW, Unicode and allocation measurements support it.
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

- ARC retain/release and object lifetime
- Array/String/Data copy-on-write, slices and retained storage
- value/reference semantics, inout/exclusivity and unsafe buffers
- throws/Result/optional behavior and cleanup
- async/await, task cancellation, actor isolation and Sendable
- generics/existentials/dynamic dispatch, ABI and deployment target
