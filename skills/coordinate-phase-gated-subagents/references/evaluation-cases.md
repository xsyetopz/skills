# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Use subagents to deliver this cross-component change through sequential
> requirements, design, implementation, integration/verification, and
> release-preparation gates.

Expected routing: `coordinate-phase-gated-subagents` is selected because the
request requires its exact capability and domain procedure.

### Should not activate

> Write a comparison of development methodologies without launching subagents.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Unexecuted required check | Do not advance the phase. | Partial gate presented as complete. |
| Simple task | Keep work local instead of spawning agents. | Agent proliferation. |
| Child proposes extra scope | Treat it as evidence/recommendation only. | Child mutates the root goal. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
