# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Current-state statement | Exact source/config/history location and revision. | Plan author assertion. |
| Task is complete | Specified diff/artifact plus boundary-appropriate checks. | Code written. |
| Migration is complete | Inventory transformed/reconciled, readers/writers switched, rollback/cleanup conditions met. | Migration command exit 0. |
| Rollout is safe | Targeted environment checks, observability, failure/rollback plan, and approval where applicable. | Unit tests. |
| Parallelism is valid | Disjoint ownership and explicit dependency/output contract. | Different task titles. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
