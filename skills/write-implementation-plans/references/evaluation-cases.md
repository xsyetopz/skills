# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Write an ordered implementation plan for the agreed change, with exact
> components, dependencies, migrations, acceptance checks, and scope exclusions.

Expected routing: `write-implementation-plans` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Execute the plan or review an existing plan only for flaws.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Small change | Keep the plan proportionate. | Architecture/rollout ceremony invented. |
| Unknown technical choice | Plan an experiment or expose decision. | Unsupported choice silently fixed. |
| Consumer paths | Include actual configs/tests/docs affected. | Plan ignores repository integration. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
