# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this Java/JVM workload with JFR/JMH while preserving
> target JDK, warmup, synchronization, ordering, exceptions, and allocation
> semantics.

Expected routing: `optimize-java-code` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Optimize Kotlin source.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Warmup | Separate startup from steady state. | Cold and warmed results mixed. |
| JMH state | Use correct scope, forks, and result consumption. | Benchmark optimized away or shares invalid state. |
| Concurrency | Verify happens-before and ordering. | Race introduced for throughput. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
