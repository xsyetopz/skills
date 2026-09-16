# Worked examples for optimizing Rust code

## Correctness-first hot loop

```rust
fn count_nonzero(bytes: &[u8]) -> usize {
    bytes.iter().filter(|&&value| value != 0).count()
}

// Compare iterator, scalar loop, and SIMD only under the target profile and
// features.
// Inspect semantics and generated code; “zero cost” is not a measurement.
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

- ownership/borrowing/lifetime/drop order and aliasing
- clone/copy/reference-counting and retained ownership
- iterators/laziness/order/errors and panic behavior
- unsafe validity, alignment, initialization, provenance and bounds
- async cancellation/drop, Send/Sync, pinning and backpressure
- atomics/locks/memory order, target features and fallback dispatch
