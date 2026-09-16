# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this Go workload with native benchmarks and profiles
> while preserving goroutine lifetime, cancellation, errors, races, and data
> ownership.

Expected routing: `optimize-go-code` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Apply Go style comments only.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Goroutine parallelism | Measure representative size and verify cancellation/ownership. | More goroutines assumed faster. |
| Slice reuse | Check aliasing and retained capacity. | Optimization mutates caller data. |
| Benchmark | Use b.N/RunParallel correctly and prevent dead-code elimination. | Harness measures setup or nothing. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
