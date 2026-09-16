# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Migrate dependency installation and tests to Bun while retaining the declared
> Node production runtime and verifying lock resolution and lifecycle scripts.

Expected routing: `migrate-js-tooling-to-bun` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Optimize JavaScript allocations without changing tooling.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Selected responsibility only | Do not replace package manager, runtime, test, and bundler together. | Toolchain scope inflation. |
| Registry/auth | Preserve existing private registry controls. | Migration drops authentication. |
| Compatibility | Add workarounds only for evidenced consumers. | Speculative Node shim. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
