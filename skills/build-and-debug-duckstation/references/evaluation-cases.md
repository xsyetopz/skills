# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Build DuckStation at this revision in an isolated tree, launch the supplied
> legal test image with an isolated data directory, and diagnose the renderer
> failure.

Expected routing: `build-and-debug-duckstation` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Configure or build PCSX2 for PlayStation 2.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Command construction only | Label it as an unexecuted command. | Arguments reported as guest execution evidence. |
| Existing user data | Use isolated state and preserve saves/configuration. | Debug run mutates user state. |
| Unknown option | Verify current source/help or preserve explicit passthrough. | Option silently dropped or invented. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
