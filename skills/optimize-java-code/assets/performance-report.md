# Java performance result

## Target

- JDK vendor and version (`java -version`), `--release`, build tool.
- JVM flags as deployed, collector (`Using ...` line), heap limits.
- OS, CPU, core count, container limits; whether the machine was shared.

## Attribution

- Workload and metric (latency percentile, throughput, B/op, pause,
  footprint, startup).
- Evidence: `jfr view ...` excerpt, GC log pause summary, JIT log line, or
  JMH row that names the cost.

## Change

- Construct card applied and the **Use when** condition it matched.
- **Do not use when** conditions checked and why they do not apply.

## Correctness

- Oracle command and result; edge, error, `null`, ordering, and
  concurrency cases covered.

## Measurement

| Benchmark | Mode | Baseline | Candidate | Unit | B/op before | B/op after |
| --- | --- | --- | --- | --- | --- | --- |
| `Class.method` | avgt | score ± error | score ± error | ns/op | n | n |

- JMH command (forks, warmup, iterations, profilers) and JSON paths.
- `scripts/jmh_compare.py` output.
- Application-level result for the same change.

## Decision

- Keep, revert, or inconclusive, with the reason. State unverified targets
  (other JDKs, operating systems, production load).
