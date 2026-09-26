# Performance change: <one-line summary>

## Target

- Metric and goal: <for example, p99 latency of /search under 200 rps>
- Workload: <input, size distribution, concurrency>
- Backend: <Kotlin/JVM; Native or JS targets listed as not measured>
- Toolchain: <Kotlin version, jvmTarget, compiler arguments>
- Runtime: <JDK version, JVM flags, kotlinx.coroutines version>
- Machine: <OS, CPU, cores; shared or dedicated>

## Attribution

- Tool and command: <JFR view / javap / JMH -prof gc / runTest>
- Finding: <frame, type, or instruction and its share before the change>

## Change

- Construct: <card name from the skill>
- Preconditions checked: <each "Use when" item and how it was confirmed>
- Counter-indications ruled out: <each "Do not use when" item>

## Correctness

- Oracle: <test command>
- Cases: <empty, boundary, non-ASCII, exception, cancellation, order>
- Result: <pass/fail output>

## Measurement

| Benchmark | Baseline ns/op ± error | Candidate ns/op ± error | B/op |
| --- | --- | --- | --- |
| <name> | <value> | <value> | <before -> after> |

- Bytecode or allocation evidence: <javap lines or bytes per call>
- Escape-analysis control: <INFO lines from -XX:-DoEscapeAnalysis or n/a>
- Application-level result: <load test or end-to-end numbers>

## Decision and limits

- Keep, revert, or inconclusive: <decision and why>
- Not verified: <backends, harnesses, JDKs, production load not run>
