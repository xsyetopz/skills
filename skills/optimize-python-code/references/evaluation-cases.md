# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this Python workload with pyperf/cProfile while
> preserving supported versions, iterator consumption, errors, identity, side
> effects, and equivalent inputs.

Expected routing: `optimize-python-code` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Apply PEP 20 readability principles without a performance goal.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Iterator optimization | Preserve single-use/eager/lazy behavior. | Candidate drops or duplicates consumption. |
| pyperf | Use stable environment and repeated runs. | One timing sample treated as proof. |
| Validation removal | Keep required checks and error behavior. | Candidate is faster by doing less. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
