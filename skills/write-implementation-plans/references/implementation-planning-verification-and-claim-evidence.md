# Verification and claim evidence for Implementation Planning

Select evidence that can discriminate the claimed property of the implementation
plan. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Current-state statement | Exact source/config/history location and revision. | Plan author assertion. |
| Task is complete | Specified diff/artifact plus boundary-appropriate checks. | Code written. |
| Migration is complete | Inventory transformed/reconciled, readers/writers switched, rollback/cleanup conditions met. | Migration command exit 0. |
| Rollout is safe | Targeted environment checks, observability, failure/rollback plan, and approval where applicable. | Unit tests. |
| Parallelism is valid | Disjoint ownership and explicit dependency/output contract. | Different task titles. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the implementation plan, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
