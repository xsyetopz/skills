# Optimization case studies for Python Interpreter Performance

## Correctness-first hot loop

```python
def count_nonzero(data: bytes) -> int:
    return sum(value != 0 for value in data)

# A manual loop or NumPy conversion may be faster for a different size/domain.
# Measure actual inputs and preserve bytes/iterator/error behavior.
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

- iterator/generator one-shot consumption and laziness
- truthiness, equality/identity, hashing, ordering, Unicode and numeric behavior
- exceptions/warnings/context manager cleanup and resource lifetime
- mutability/aliasing/copying and retained objects
- GIL/free-threaded build/C-extension thread safety
- descriptor/property/import/module and supported-version behavior
