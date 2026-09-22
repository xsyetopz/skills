# Optimization case studies for Dotnet Csharp Performance

## Correctness-first hot loop

```csharp
static int CountNonZero(ReadOnlySpan<byte> bytes)
{
    var count = 0;
    foreach (var value in bytes)
        count += value != 0 ? 1 : 0;
    return count;
}

// Use SIMD or unsafe code only after matched measurement and bounds/CPU
// fallback proof. Span removes a copy only when the caller can supply a view.
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

- effective target framework/runtime/JIT/AOT/GC/build properties
- allocation, boxing, closure/state-machine, string and collection behavior
- `Span<T>`/`Memory<T>` lifetime and ref-safety
- async/cancellation/context, `Task` versus `ValueTask`, pooling and
  double-consumption
- threading, memory model, locks/channels and disposal
- P/Invoke marshalling, pinning, callbacks, native ownership and teardown
