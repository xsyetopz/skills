# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this TypeScript source for its configured runtime/build
> target while preserving emitted runtime behavior, strict type/API contracts,
> async completion, and equivalent work.

Expected routing: `optimize-typescript-code` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Migrate TypeScript to another runtime.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Type check | Run project compiler options as well as runtime tests. | Type stripping presented as type checking. |
| Emission target | Measure generated code in actual runtime. | Different target/module results compared. |
| Async | Await equal operations and preserve rejection. | Candidate exits early. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
