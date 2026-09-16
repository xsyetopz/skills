# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Requirement reflects user intent | Trace to explicit current request or approved decision. | Existing code alone. |
| Acceptance criterion is testable | Defined setup, action, observable outcome, and failure distinction. | “Works correctly” or a source-code marker. |
| External obligation applies | Exact standard/API/version and boundary mapping. | Adjacent product documentation. |
| Compatibility must be preserved | Declared stable contract/support policy and affected consumer evidence. | An old alias or test alone. |
| Performance requirement is valid | Authoritative threshold, SLO, capacity target, or user decision with measurement conditions. | A guessed number or benchmark from another workload. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
