# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, p50 time per parse of a 1 MB log, or
  mallocs per request>
- Workload: <input, size distribution, tasks or threads>
- Environment: <OS, CPU, `swift --version`, load average during runs>
- Build: <configuration and flags from `swift build -c release -v`:
  -O/-Osize, WMO, CMO, library evolution; deployment target>

## Attribution

- Tool and command: <xctrace Time Profiler / package-benchmark /
  counting hooks / -emit-sil / -emit-assembly>
- Finding: <function, counter, or instruction pattern and its share
  before the change>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>
- PERF/SAFETY comments added: <file:line list or none>
- API or ABI impact: <final, @inlinable, @frozen, signature changes,
  or none>

## Correctness

- Oracle: <command>
- Cases: <empty, one element, boundary sizes, Unicode (combining marks,
  ZWJ emoji, flags, CRLF), overflow, error and cancellation paths>
- Result: <output>

## Measurement

| Benchmark | Baseline | Candidate | Mallocs / retains |
| --- | --- | --- | --- |
| <name> | <p50 and p90 with unit> | <p50 and p90 with unit> | <a -> b> |

- Command: <swift package benchmark baseline compare ... / harness>
- Assembly or SIL evidence: <symbol, pattern, count before -> after>
- Application-level result: <before/after with spread>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <Linux, other architectures, older OS versions,
  Instruments templates not run>
