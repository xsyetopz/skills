# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, wall time of `tool convert big.csv`, or
  allocator calls per request>
- Workload: <input, size distribution, threads>
- Environment: <OS, CPU, `cc --version`, SDKROOT or sysroot, libc>
- Build: <C standard, optimization level, -mcpu/-march, LTO, PGO,
  sanitizer flags, linker; unchanged or changed by this work>

## Attribution

- Tool and command: <sample / xctrace / perf / counting wrapper / -S>
- Finding: <frame, count, or instruction pattern and its share before
  the change>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>
- Invariants documented in code: <restrict contracts, ownership,
  alignment, buffer sizes; file:line or none>

## Correctness

- Oracle: <command>
- Cases: <empty, one element, boundary lengths, overlap, INT_MAX and
  INT_MIN, NaN and -0.0 when floats change, error paths>
- Sanitizers: <ASan+UBSan command and result>
- Leaks: <leaks --atExit or ASan result>

## Measurement

| Benchmark | Baseline | Candidate | Calls or instructions |
| --- | --- | --- | --- |
| <id> | <median or mean ± σ> | <median or mean ± σ> | <before -> after> |

- Command: <verify.sh time ..., hyperfine ...>
- Repeats: <runs, and whether the machine was shared>
- Application-level result: <before/after with ± range>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <other compilers, targets, CPUs, perf counters, x86
  dispatch path>
