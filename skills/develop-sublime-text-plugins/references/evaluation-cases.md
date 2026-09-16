# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Implement this Sublime Text command using the embedded Python version, Edit
> lifetime, view freshness, unload cleanup, host tests, and package layout.

Expected routing: `develop-sublime-text-plugins` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Format an ordinary Python script.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Edit token | Use it only during the command callback. | Edit object retained asynchronously. |
| Stub test | Label it as stub-based evidence. | Stub pass reported as Sublime host execution. |
| Reload | Clean up owned timers/listeners only. | Existing package/user state removed. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
