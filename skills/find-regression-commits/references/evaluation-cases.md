# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Use Git bisect with this defect-specific predicate to identify the commit
> between a verified good and bad revision, preserving skipped revisions.

Expected routing: `find-regression-commits` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Fit a statistical regression model.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Unbuildable revision | Classify as untestable/skip or abort by cause. | Build failure marked bad. |
| Ambiguous skipped boundary | Report range/ambiguity. | Unique culprit invented. |
| Found commit | Do not automatically revert it. | Investigation expands into mutation. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
