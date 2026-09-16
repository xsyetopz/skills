# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Behavior was never required | No authoritative support source plus history/context showing speculative introduction and no real consumer evidence. | Agent statement or empty grep alone. |
| Support is retired | Explicit policy/decision/release milestone that permits removal and consumer/data handling satisfied. | Deprecated annotation alone. |
| No packaged/runtime alias remains | Artifact/export/registration inspection and negative boundary test. | Source function deleted. |
| Supported behavior preserved | Contract-focused tests and package/integration checks. | Compilation only. |
| Data migration safe | Inventory, transformation, validation, rollback, and read-path evidence. | New parser unit tests. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
