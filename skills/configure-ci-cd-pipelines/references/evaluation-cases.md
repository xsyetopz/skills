# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Add a GitHub Actions build and test workflow for this repository, preserving
> fork security, artifact identity, and existing deploy approval.

Expected routing: `configure-ci-cd-pipelines` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Change branch protection to require two reviewers without editing CI jobs.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Fork pull request | No privileged secrets or write token reach untrusted code. | Privilege crosses trust boundary. |
| Artifact promotion | Promote the exact built revision and immutable artifact. | Release job rebuilds different source. |
| Provider syntax | Validate against the selected provider/version. | GitLab or remembered syntax copied into GitHub Actions. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
