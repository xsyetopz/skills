# Evaluation cases

These cases are maintained probes for selection and instruction compliance. They
are not claimed passes. Run them with the exact target model and harness in an
isolated workspace, compare against a no-skill or prior-skill baseline, and
inspect produced files and command evidence rather than grading prose alone.

## Selection cases

### Should activate

> Profile and optimize this Rust workload under the target profile/features
> while preserving ownership, lifetimes, errors, synchronization, target CPU,
> and safe behavior.

Expected routing: `optimize-rust-code` is selected because the request requires
its exact capability and domain procedure.

### Should not activate

> Introduce unsafe code solely because it may be faster.

Expected routing: do not select this skill solely because the prompt shares a
keyword. Use the neighboring capability or ordinary agent behavior instead.

## Conformance cases

| Scenario | Required behavior | Failure detected |
| --- | --- | --- |
| Unsafe | Require measured need, documented invariants, and tests/Miri/sanitizers where applicable. | Unsafe asserted correct by compilation. |
| Feature/profile | Match target-cpu, LTO, panic, allocator, and features. | Different builds compared. |
| Borrowing/allocation | Preserve observable lifetime and ownership. | Borrowed data outlives owner. |

## Enterprise evaluation record

For each run, retain the prompt, model and harness versions, skill revision,
repository/input revision, effective tools and permissions, outputs/diffs,
commands and observations, token/time measurements when available, grader or
human review basis, and every unexecuted boundary. Repeat nondeterministic cases
and report variance; do not turn a single pass or selection event into a general
success claim.
