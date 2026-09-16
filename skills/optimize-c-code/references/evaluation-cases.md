# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this C hot path under the declared compiler/standard and
> representative workload while preserving ABI, ownership, errors, and
> undefined-behavior constraints.

Expected routing: `optimize-c-code` is selected because the request requires its
exact capability and domain procedure.

### Should not activate

> Refactor C formatting without a performance objective.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Mismatched work | Benchmark identical inputs, outputs, setup boundary, and build flags. | Candidate does less work. |
| Integer/aliasing edge | Use correctness oracles and sanitizers where applicable. | Faster undefined behavior. |
| Single run | Repeat and report distribution/stability. | One-run superiority claim. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
