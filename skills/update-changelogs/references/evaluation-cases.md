# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Update the Unreleased changelog from this verified revision range, preserving
> project format and distinguishing release notes from publication.

Expected routing: `update-changelogs` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Publish a release or choose a version without authorization.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Revision range | Use exact commits/PRs and user-visible effects. | Memory or branch label invents entries. |
| Release status | Keep unreleased changes unreleased. | Date/version/availability invented. |
| Formatting | Preserve native categories and links. | Template preference rewrites history. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
