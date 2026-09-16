# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Refactor this Rust module using explicit contracts, purposeful names, and the
> simplest design that preserves behavior.

Expected routing: `apply-pep20-to-codebases` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Run the Python formatter on this file without changing its design.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Non-Python codebase | Apply principles without Python syntax, PEP 8, or Python tools. | Category substitution. |
| Justified abstraction | Retain it when ownership or extension constraints require it. | Simplicity used as a blanket deletion rule. |
| Naming change | Verify public/API compatibility before renaming. | Aphorism overrides an established contract. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
