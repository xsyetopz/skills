# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Create scoped AGENTS.md instructions from inspected repository commands, file
> ownership, generated boundaries, precedence, and the named agent client.

Expected routing: `write-agents-md` is selected because the request requires its
exact capability and domain procedure.

### Should not activate

> Create a reusable Agent Skill package.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Scope | Place instructions at the narrowest applicable tree. | Nested rules overwrite root globally. |
| Command | Verify it exists and working directory/arguments. | Plausible command copied from another repo. |
| Stale current text | Update from source/config evidence. | Existing AGENTS.md treated as infallible. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
