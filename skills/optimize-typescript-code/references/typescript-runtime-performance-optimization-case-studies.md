# Optimization case studies for Typescript Runtime Performance

## Correctness-first hot loop

```typescript
export function countNonZero(bytes: Uint8Array): number {
  let count = 0;
  for (let i = 0; i < bytes.length; i++) count += bytes[i] !== 0 ? 1 : 0;
  return count;
}

// Type annotations erase. Runtime performance depends on emitted JS, target
// runtime and data. Keep `tsc --noEmit`/declaration checks separate.
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

- TypeScript erasure versus emitted JavaScript behavior
- tsconfig/module/target/downlevel helpers and bundler transformations
- type inference/generic/conditional-type complexity and public declaration API
- JavaScript coercion, async ordering, errors, objects and buffers
- incremental build/cache/project references and generated declarations
- source-map/profile attribution and runtime-specific APIs
