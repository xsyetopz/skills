# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, p99 latency of /search under 200 rps>
- Workload: <input, size distribution, concurrency>
- Environment: <OS, CPU, runtime and version (node/bun/browser), flags>
- Build: <bundler, transpile target, minification, NODE_ENV>

## Attribution

- Tool and command: <node --cpu-prof / --trace-gc / DevTools Performance>
- Finding: <frame and its inclusive share, GC count, or event-loop delay>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>
- Invariant comments added: <file:line list or none>

## Correctness

- Oracle: <test command>
- Cases: <empty, boundary, NaN/-0, holes, Unicode, errors, rejections>
- Result: <pass/fail output>

## Measurement

| Pair | Runtime | Baseline median (spread) | Candidate median (spread) | Alloc |
| --- | --- | --- | --- | --- |
| <name> | <node 26.x> | <ns/op (p90)> | <ns/op (p90)> | <B -> B> |

- Harness and command: <for example sh verify.sh measure, mitata>
- Process isolation: <separate process per side, or why not needed>
- Application-level result: <load-test or trace numbers before/after>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <runtimes, browsers, versions, platforms not run>
