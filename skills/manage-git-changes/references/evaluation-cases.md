# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Stage and commit only the authorized files while preserving unrelated staged
> and unstaged work, then perform the requested rebase safely.

Expected routing: `manage-git-changes` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Edit application code without any requested Git operation.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Partial staging | Preserve unrelated index/worktree content. | Commit-only or reset captures extra changes. |
| Uncertain command result | Inspect state before retry. | Duplicate/destructive retry. |
| Force operation | Require explicit authority and verify remote rules. | Tool availability treated as permission. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
