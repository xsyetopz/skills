# Worked examples for optimizing Kotlin code

## Correctness-first hot loop

```kotlin
fun countNonZero(bytes: ByteArray): Int {
    var count = 0
    for (value in bytes) if (value.toInt() != 0) count++
    return count
}

// `bytes.asSequence().count { ... }` is not automatically faster. It may
// allocate
// iterators and changes laziness/exception timing in larger pipelines.
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

- backend and compiler/plugin configuration
- nullability, exceptions, inline/value classes and boxing
- collections/sequences/lazy evaluation and iteration order
- coroutines, structured concurrency, cancellation, context and dispatchers
- Java interop/platform types and SAM/reflection behavior
- Kotlin/Native ownership/memory or JS runtime semantics when selected
