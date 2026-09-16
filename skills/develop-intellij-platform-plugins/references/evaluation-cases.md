# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Implement this IntelliJ Platform plugin feature with PSI freshness, read/write
> actions, undo, disposal, target IDE tests, and package verification.

Expected routing: `develop-intellij-platform-plugins` is selected because the
request requires its exact capability and domain procedure.

### Should not activate

> Refactor a standalone Kotlin CLI.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Async PSI result | Revalidate element/document before write. | Stale PSI mutation. |
| Write operation | Use write command/undo mechanism. | Direct background mutation. |
| Compatibility | Keep declared IDE range unless user changes it. | Tests made green by broad version shims. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
