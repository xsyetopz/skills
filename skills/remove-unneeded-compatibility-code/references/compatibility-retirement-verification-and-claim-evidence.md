# Verification and claim evidence for Compatibility Retirement

Select evidence that can discriminate the claimed property of the compatibility
removal. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Behavior was never required | No authoritative support source plus history/context showing speculative introduction and no real consumer evidence. | Agent statement or empty grep alone. |
| Support is retired | Explicit policy/decision/release milestone that permits removal and consumer/data handling satisfied. | Deprecated annotation alone. |
| No packaged/runtime alias remains | Artifact/export/registration inspection and negative boundary test. | Source function deleted. |
| Supported behavior preserved | Contract-focused tests and package/integration checks. | Compilation only. |
| Data migration safe | Inventory, transformation, validation, rollback, and read-path evidence. | New parser unit tests. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the compatibility removal, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
