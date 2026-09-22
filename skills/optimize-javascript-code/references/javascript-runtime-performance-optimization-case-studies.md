# Optimization case studies for Javascript Runtime Performance

## Correctness-first hot loop

```javascript
function countNonZero(bytes) {
  let count = 0;
  for (let i = 0; i < bytes.length; i++) count += bytes[i] !== 0;
  return count;
}

// Keep the same TypedArray/Array domain, coercion and detached-buffer behavior
// when comparing alternatives.
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

- coercion, `NaN`, `-0`, BigInt, Unicode and property access
- object identity, prototypes, getters/setters and enumeration order
- Promises, microtasks/macrotasks, cancellation/AbortSignal and event-loop
  fairness
- exceptions/rejections, stack and async context
- typed arrays/buffer views, detachment and shared memory
- runtime/browser/Node API and module-format compatibility
