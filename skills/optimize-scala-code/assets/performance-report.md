# Scala performance result

## Target

- Objective and metric: <ns/op | p99 latency | B/op | live heap | RSS>
- Workload and input: <benchmark name, input size, representative source>
- Toolchain: Scala <3.x.y | 2.13.z>, backend <JVM | Scala.js | Native>,
  JDK <vendor version>, build <scala-cli x | sbt x>, CPU <model>, OS <x>
- Compiler options and JVM flags: <scalacOptions, -Xmx, GC, -XX flags>

## Attribution

- Profile command: <JFR recording, JMH -prof gc, async-profiler>
- Finding: <method, hot-method share, allocation-by-class share>

## Change

- Construct card: <reference file and card name>
- Use when conditions met: <evidence>
- Do not use when conditions excluded: <evidence>
- Bytecode evidence (if the card names one): <javap lines>

## Correctness

- Oracle: <test name and command>, result <pass/fail>
- Edge cases: <empty, boundary, overflow, laziness, ordering, duplicates,
  exceptions, execution context>

## Measurement

- Command: <scala-cli --power run --jmh ... -- -prof gc ...>
- JMH output:

```text
<paste Score, Error, Units for ns/op and gc.alloc.rate.norm rows>
```

- Application-level result: <load test, service metric>

## Decision

- Keep, revert, or inconclusive: <decision and reason>
- Not verified: <other backends, JDKs, Scala versions, production profile>
