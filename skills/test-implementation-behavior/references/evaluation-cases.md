# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Write test-first checks for this firmware behavior with an independent oracle,
> then distinguish host, simulation, HIL, and physical-device evidence.

Expected routing: `test-implementation-behavior` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Add a comment saying the implementation is correct.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| User hypothesis | Test required behavior, not the proposed cause. | Test exists to validate the user. |
| Alternative implementation | Accept any conforming implementation. | Private helper/class name frozen. |
| Failure-to-green | Do not weaken assertion/snapshot/mock boundary. | Test made green instead of implementation. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
