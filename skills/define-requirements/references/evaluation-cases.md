# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Define observable behavior, failures, state transitions, constraints, and
> acceptance criteria for the requested import feature.

Expected routing: `define-requirements` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Choose the service architecture for complete requirements that already exist.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Unknown threshold | Leave unresolved or measure; do not invent a number. | Invented acceptance threshold. |
| Current implementation | Treat it as evidence, not desired behavior. | State/goal conflation. |
| User causal claim | Separate hypothesis from requested result. | Requirement encodes an unverified explanation. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
