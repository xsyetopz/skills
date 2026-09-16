# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Create an Agent Skill for this repeated workflow with sufficient references,
> tested scripts, realistic evaluation cases, and native Codex metadata.

Expected routing: `create-agent-skills` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Implement the task described by an already installed skill without changing
> the skill package.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Useful existing asset | Retain or repair it after inspecting consumers. | Asset deleted to simplify packaging. |
| Description near-miss | Do not trigger on neighboring tasks. | Keyword-only routing. |
| Evaluation | Compare skill and baseline outputs with held-out cases. | Static validation presented as effectiveness proof. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
