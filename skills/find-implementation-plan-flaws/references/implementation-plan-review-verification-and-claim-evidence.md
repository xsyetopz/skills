# Verification and claim evidence for Implementation Plan Review

Select evidence that can discriminate the claimed property of the
implementation-plan review. Run the smallest sufficient check first. Broaden
only when another contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Plan step is feasible | Matching current interface/config/tool command and prerequisites. | Plausible prose. |
| Dependency order is valid | Producer output and consumer preconditions mapped. | Numbered order alone. |
| Migration preserves data/contracts | Schema/data transformation, validation, coexistence, rollback, and consumer evidence. | New-schema unit tests. |
| Verification is sufficient | Each changed contract mapped to a discriminating check. | “Run all tests.” |
| Finding has material consequence | Demonstrated failure, scope, security, data, operability, or review impact. | Reviewer preference. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the implementation-plan review, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
