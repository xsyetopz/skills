# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Update repository setup and API usage documentation from current source and
> commands, preserving meaning outside the requested section.

Expected routing: `document-codebases` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Update AGENTS.md rules for coding agents.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Formatting-only request | Do not change technical meaning. | Formatting authorizes semantic rewrite. |
| Command example | Execute or otherwise verify it in applicable environment. | Plausible command invented. |
| Generated docs | Edit source/generator rather than output when established. | Generated file patched directly. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
