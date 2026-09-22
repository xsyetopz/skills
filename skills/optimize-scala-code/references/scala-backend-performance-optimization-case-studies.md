# Optimization case studies for Scala Backend Performance

## Correctness-first hot loop

```scala
def countNonZero(bytes: Array[Byte]): Int = {
  var count = 0
  var i = 0
  while (i < bytes.length) {
    if (bytes(i) != 0) count += 1
    i += 1
  }
  count
}

// This may beat a collection pipeline in a hot JVM loop, but benchmark the
// actual Scala/JDK and preserve collection/effect semantics.
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

- strict/lazy collections, views, iterators and repeated traversal
- type erasure, boxing, specialization and generic dispatch
- exceptions, `Option`/`Either`/effects and short-circuiting
- Futures/execution contexts or effect runtime cancellation/resource behavior
- implicit/given resolution, conversions and allocation
- backend differences among JVM, Scala.js, Native
