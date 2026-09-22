# Verification and claim evidence for Behavioral Requirements

Select evidence that can discriminate the claimed property of the behavioral
requirement set. Run the smallest sufficient check first. Broaden only when
another contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Requirement reflects user intent | Trace to explicit current request or approved decision. | Existing code alone. |
| Acceptance criterion is testable | Defined setup, action, observable outcome, and failure distinction. | “Works correctly” or a source-code marker. |
| External obligation applies | Exact standard/API/version and boundary mapping. | Adjacent product documentation. |
| Compatibility must be preserved | Declared stable contract/support policy and affected consumer evidence. | An old alias or test alone. |
| Performance requirement is valid | Authoritative threshold, SLO, capacity target, or user decision with measurement conditions. | A guessed number or benchmark from another workload. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the behavioral requirement set, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
