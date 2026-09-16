# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Create and minimize an independently runnable reproduction of this race while
> preserving the same failure signature and exact run command.

Expected routing: `reproduce-software-bugs` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Fix the production bug without creating a reproduction.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Reduction | Recheck signature after every removal. | Setup failure replaces original defect. |
| External dependency | Pin or replace only when the boundary remains. | Mock removes the failing integration. |
| Nondeterminism | Record controlled repetition and conditions. | One lucky failure/pass treated as stable. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
