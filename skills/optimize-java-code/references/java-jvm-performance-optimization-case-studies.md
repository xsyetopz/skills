# Optimization case studies for Java JVM Performance

## Correctness-first hot loop

```java
static int countNonZero(byte[] data) {
    int count = 0;
    for (byte value : data) if (value != 0) count++;
    return count;
}

// Compare loops/Vector API/streams only with the target JDK and same semantics.
// Do not infer steady-state latency from a single in-process stopwatch.
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

- JMM happens-before, synchronization, volatile/atomics and safe publication
- exceptions, ordering, null behavior and API compatibility
- boxing, streams/lambdas, collections and allocation
- JIT tiering, deoptimization, escape analysis and dead-code elimination
- GC/heap/reference retention and classloader lifetime
- reflection, modules, serialization and deployment/JDK compatibility
