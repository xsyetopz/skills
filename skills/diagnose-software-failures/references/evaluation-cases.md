# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Reproduce this intermittent crash, locate the first incorrect state, and run
> experiments that distinguish the leading causes before changing code.

Expected routing: `diagnose-software-failures` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Apply this already established one-line fix.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| User hypothesis | Test it against alternatives. | Tautological reproduction confirms the prompt. |
| Transient failure | Diagnose protocol/idempotency before retries. | Retry reflex hides root cause. |
| Harness failure | Reproduce below wrapper where practical. | Harness behavior attributed to target. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
