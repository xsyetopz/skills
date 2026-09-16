# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Implement this Neovim Lua plugin command with buffer identity, changedtick
> checks, owned autocmd groups, job cancellation, tests, and help.

Expected routing: `develop-neovim-plugins` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Add one personal key mapping to my local config.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Stale callback | Reject result when buffer/generation changed. | Current buffer edited by old work. |
| Reload | Clear only owned groups/handles and register idempotently. | Duplicate callbacks after reload. |
| Vim-only API | Do not claim Neovim support from adjacent docs. | Product substitution. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
