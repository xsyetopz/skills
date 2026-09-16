# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Same defect reproduced | Same failure signature under recorded input/revision/config, not merely any error. | Generic exit failure. |
| Hypothesis supported | Predicted differentiating observation occurs and alternatives are contradicted. | Temporal correlation. |
| Root cause established | Causal path from triggering condition through first divergence to symptom, with owning invariant. | A nearby suspicious line. |
| Race fixed | Relevant schedule/state invariant checked repeatedly and with race/sanitizer tooling where applicable. | Added sleep or one pass. |
| Memory issue fixed | Independent behavior test plus appropriate sanitizer/ownership checks. | No crash in a short run. |
| Production issue resolved | Authorized deployment and production/representative observation at the failed boundary. | Local unit test alone. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
