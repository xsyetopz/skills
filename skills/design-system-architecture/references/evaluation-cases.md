# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Design component boundaries, interfaces, dependency direction, and state
> ownership for this system under the stated reliability and deployment
> constraints.

Expected routing: `design-system-architecture` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Rename one local variable without changing system structure.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Existing justified boundary | Preserve it unless evidence requires change. | Greenfield default overwrites architecture. |
| Similar code | Inspect invariants and change patterns before abstracting. | Premature abstraction. |
| Review-only request | Propose changes without mutating code. | Design authority treated as edit authority. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
