# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Write or repair justfile recipes that wrap existing project commands with
> correct parameters, dependencies, quoting, working directory, and exit
> propagation.

Expected routing: `write-justfiles` is selected because the request requires its
exact capability and domain procedure.

### Should not activate

> Replace the project build system with just.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Underlying failure | Propagate nonzero status. | Later successful command masks failure. |
| Quoting/arguments | Preserve exact argv semantics across selected shell. | String interpolation changes arguments. |
| Unavailable just | Report parser/execution unverified. | Text inspection presented as native validation. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
