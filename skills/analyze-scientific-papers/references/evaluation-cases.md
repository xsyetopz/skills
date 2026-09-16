# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Find primary studies on whether intervention X changes outcome Y in population
> Z, compare methods and effect estimates, and identify corrections or
> replications.

Expected routing: `analyze-scientific-papers` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Reformat this supplied bibliography in APA style without researching the
> papers.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Abstract-only source | Treat methods and unavailable results as unknown; do not infer them from metadata. | Metadata presented as full-paper evidence. |
| Conflicting populations | Separate applicability before synthesis. | Results transferred across populations without support. |
| Retraction or correction | Follow and report the later record. | Stale original result presented as current evidence. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
