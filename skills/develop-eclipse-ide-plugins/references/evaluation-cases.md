# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Implement this Eclipse plugin action using the declared target platform,
> workspace scheduling rules, SWT/JFace lifecycle, Tycho tests, and p2
> packaging.

Expected routing: `develop-eclipse-ide-plugins` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Change an Eclipse color preference without developing a plugin.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| UI callback after job | Re-resolve state and keep resources alive until callback. | Disposed/stale resource access. |
| Workspace mutation | Use the appropriate Job and scheduling rule. | Background write violates workspace rules. |
| Standalone Java test | Report it as logic evidence only. | Standalone compilation reported as Eclipse host proof. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
