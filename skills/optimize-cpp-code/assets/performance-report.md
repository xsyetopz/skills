# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, time per request parse, or
  allocations per frame>
- Workload: <input, size distribution, threads>
- Environment: <OS, CPU, `c++ --version`, `_LIBCPP_VERSION` or
  library, SDKROOT or sysroot>
- Build: <-std, -O level, -march/-mcpu, LTO, hardening mode,
  exceptions/RTTI flags, deployment target>

## Attribution

- Tool and command: <xctrace / perf / counting operator new /
  copy-move counter / -S>
- Finding: <function or count and its share before the change>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>
- PERF comments added: <file:line list with the lifetime or ordering
  argument, or none>

## Correctness

- Oracle: <command>
- Cases: <empty, one element, boundary values, embedded NUL,
  non-ASCII, missing keys, error paths, tie order>
- Sanitizers: <ASan/UBSan command and result, or not run>

## Measurement

| Benchmark | Baseline | Candidate | Counts or assembly |
| --- | --- | --- | --- |
| <id> | <median, spread, unit> | <median, spread, unit> | <before -> after> |

- Command: <harness, Google Benchmark, or hyperfine command>
- Application-level result: <before/after with spread>
- Machine load: <quiet or shared; reruns performed>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <other standard libraries, compilers, architectures,
  deployment targets, sanitizers>
