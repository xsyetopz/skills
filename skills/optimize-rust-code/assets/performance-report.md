# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, time per parse of a 1 MB log, or
  allocations per request>
- Workload: <input, size distribution, threads>
- Environment: <OS, CPU, `rustc -Vv`, `cargo -V`>
- Build: <profile keys (opt-level, lto, codegen-units, panic, debug),
  RUSTFLAGS, target-cpu, features>

## Attribution

- Tool and command: <samply / counting allocator / Criterion / --emit asm>
- Finding: <function or count and its share before the change>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>
- PERF/SAFETY comments added: <file:line list or none>

## Correctness

- Oracle: <command>
- Cases: <empty, one element, boundary lengths, non-ASCII, error and
  panic paths>
- Result: <output>

## Measurement

| Benchmark | Baseline | Candidate | Allocations or calls |
| --- | --- | --- | --- |
| <id> | <[low est high] unit> | <[low est high] unit> | <before -> after> |

- Command: <cargo bench ... -- --baseline before, or hyperfine ...>
- Assembly evidence: <symbol, pattern, count before -> after>
- Application-level result: <before/after with ± range>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <Miri, nightly, other targets, Xcode-only profilers>
