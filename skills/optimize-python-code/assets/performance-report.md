# Python performance result

## Target

- Interpreter: `python -VV` output; GIL or free-threaded
  (`Py_GIL_DISABLED`, `sys._is_gil_enabled()`); JIT state.
- Supported Python range (`requires-python`), OS, CPU, lockfile revision.
- Metric and workload: what was measured, input sizes, and why they are
  representative.

## Attribution

- Command (cProfile, tracemalloc diff, `-X importtime`, `perf`) and the rows
  that attribute the cost, with `ncalls`/`tottime`/`cumtime` or bytes.

## Change

- Construct card applied and its **Use when** conditions, checked.
- Invariants recorded in code comments.

## Equivalence

- Oracle command and result. Inputs covered: empty, one-shot iterator,
  duplicates, ties, errors, boundaries.

## Measurement

- Deterministic card metric before and after (calls, executed
  instructions, comparisons, traced peak bytes).
- pyperf commands, options (`--fast`, `--rigorous`, `--inherit-environ`),
  and `compare_to --table` rows with mean ± std dev and significance.
- Application-level result for the same workload.

## Decision

- Keep, revert, or inconclusive, with the reason.
- Not verified: platforms, builds, or versions not run.
