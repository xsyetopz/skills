# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this JavaScript workload in the named browser or server
> runtime while preserving coercion, ordering, async behavior, errors, and
> equivalent work.

Expected routing: `optimize-javascript-code` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Migrate the runtime to Bun.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Runtime/version | Measure the actual target engine. | Node result transferred to browser. |
| Async completion | Await equivalent work and error paths. | Candidate returns before work completes. |
| TypeScript-only fixture | Do not claim JavaScript coverage from TS type checks. | Language evidence conflated. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
