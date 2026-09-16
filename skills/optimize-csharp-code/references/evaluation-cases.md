# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this C#/.NET workload with BenchmarkDotNet and runtime
> diagnostics while preserving target framework, async/cancellation,
> allocations, interop lifetime, and behavior.

Expected routing: `optimize-csharp-code` is selected because the request
requires its exact capability and domain procedure.

### Should not activate

> Upgrade an unrelated project to .NET 10.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| ValueTask/pooling | Prove ownership and reuse constraints. | Allocation reduction corrupts lifetime. |
| Interop | Keep handles/delegates/native buffers alive correctly. | Faster use-after-free. |
| Effective config | Inspect evaluated MSBuild/runtime settings. | Raw project XML treated as runtime fact. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
