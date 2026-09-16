# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Remove this compatibility alias and fallback after verifying it was never
> required or is explicitly retired, preserving supported consumers and unique
> behavior.

Expected routing: `remove-unneeded-compatibility-code` is selected because the
request requires its exact capability and domain procedure.

### Should not activate

> Delete old-looking code without evidence about consumers or support policy.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Agent-added shim plus test | Neither creates product authority by itself. | Invented compatibility becomes permanent. |
| Stable external consumer | Preserve according to declared contract even if grep is empty. | Local search treated as global proof. |
| Wrapper removal | Retain unique validation/error/cleanup behavior. | Thin wrapper deleted with required semantics. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
