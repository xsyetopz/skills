# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A boundary is needed | Scenarios showing distinct ownership, lifecycle, deployment, trust, scaling, substitution, or failure requirements. | A diagram that looks cleaner. |
| A service can meet availability goals | Failure model, dependency budgets, deployment/rollback, capacity, and operational evidence. | Successful local request. |
| A cache improves the system | Representative measurements plus invalidation, consistency, bounds, and recovery design. | Assumption that memory is faster. |
| A protocol abstraction is lossless enough | Mapping of all required operations, errors, streaming/cancellation, versioning, and escape hatches. | Common method names. |
| Migration is safe | Consumer inventory, data transformation/validation, coexistence, rollback, and reconciliation evidence. | Unit tests for new code alone. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
