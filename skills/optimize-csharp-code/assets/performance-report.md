# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, p99 latency of /search under 200 rps>
- Workload: <input, size distribution, concurrency>
- Environment: <OS, CPU, runtime version, SDK, JIT/AOT, GC mode>
- Evaluated build properties: <dotnet msbuild -getProperty output>

## Attribution

- Tool and command: <dotnet-counters / dotnet-trace / BenchmarkDotNet>
- Finding: <frame or counter and its share before the change>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>
- PERF/SAFETY comments added: <file:line list or none>

## Correctness

- Oracle: <test command>
- Cases: <empty, boundary, overflow, error, concurrency>
- Result: <pass/fail output>

## Measurement

| Benchmark | Baseline mean ± error | Candidate mean ± error | Allocated |
| --- | --- | --- | --- |
| <name> | <value> | <value> | <before -> after> |

- Job and command: <for example --job default --filter '*Search*'>
- Application-level result: <load-test numbers before/after>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <platforms, runtimes, diagnosers not run>
