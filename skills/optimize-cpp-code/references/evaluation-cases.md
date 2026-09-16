# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this C++ path while preserving the selected standard,
> lifetime, iterator/reference validity, exceptions, ABI, concurrency, and
> workload.

Expected routing: `optimize-cpp-code` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Optimize C-only source.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Container optimization | Verify invalidation and ownership. | Dangling references improve timing. |
| Build profile | Match flags, LTO, features, and allocator. | Debug/release numbers compared. |
| Benchmark framework | Separate setup from measured operation. | Initialization dominates result. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
