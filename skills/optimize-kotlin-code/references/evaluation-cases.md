# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this Kotlin workload for its declared backend while
> preserving coroutine cancellation, collection/lazy semantics, nullability,
> exceptions, and target behavior.

Expected routing: `optimize-kotlin-code` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Optimize Java source.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Backend | Use JVM tools only for Kotlin/JVM. | JVM evidence generalized to Native/JS. |
| Sequence conversion | Measure allocations and preserve evaluation timing. | Laziness changes errors/effects. |
| Coroutines | Preserve structured concurrency and cancellation. | Detached work improves latency artificially. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
