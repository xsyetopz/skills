# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Plan step is feasible | Matching current interface/config/tool command and prerequisites. | Plausible prose. |
| Dependency order is valid | Producer output and consumer preconditions mapped. | Numbered order alone. |
| Migration preserves data/contracts | Schema/data transformation, validation, coexistence, rollback, and consumer evidence. | New-schema unit tests. |
| Verification is sufficient | Each changed contract mapped to a discriminating check. | “Run all tests.” |
| Finding has material consequence | Demonstrated failure, scope, security, data, operability, or review impact. | Reviewer preference. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
