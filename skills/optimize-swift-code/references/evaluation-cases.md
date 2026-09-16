# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this Swift workload on the specified target while
> preserving copy-on-write, ownership, exclusivity, Unicode, errors, and actor
> isolation.

Expected routing: `optimize-swift-code` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Change deployment targets without a performance request.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| CoW | Verify uniqueness/sharing and mutation semantics. | Hidden copy or shared mutation. |
| String/Data conversion | Measure allocations and preserve indexing/Unicode. | Byte assumptions corrupt text. |
| Concurrency | Preserve actor/sendability contracts. | Isolation removed for speed. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
