# Verification and claim evidence for Failure Investigation

Select evidence that can discriminate the claimed property of the root-cause
investigation. Run the smallest sufficient check first. Broaden only when
another contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Same defect reproduced | Same failure signature under recorded input/revision/config, not merely any error. | Generic exit failure. |
| Hypothesis supported | Predicted differentiating observation occurs and alternatives are contradicted. | Temporal correlation. |
| Root cause established | Causal path from triggering condition through first divergence to symptom, with owning invariant. | A nearby suspicious line. |
| Race fixed | Relevant schedule/state invariant checked repeatedly and with race/sanitizer tooling where applicable. | Added sleep or one pass. |
| Memory issue fixed | Independent behavior test plus appropriate sanitizer/ownership checks. | No crash in a short run. |
| Production issue resolved | Authorized deployment and production/representative observation at the failed boundary. | Local unit test alone. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the root-cause investigation, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
