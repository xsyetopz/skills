# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Same bug reproduced | Reduced case exhibits defining signature and control/sanity checks distinguish alternatives. | Any failure. |
| Dependency is unnecessary | Case still reproduces after removal in a fresh run. | Source search suggests unused. |
| Reproducer is self-contained | Fresh checkout/copy setup and run succeeds to the target failure with declared prerequisites. | Works on author’s existing machine. |
| Sanitization preserved defect | Same internal condition/signature under synthetic data. | Data looks similar. |
| Race is reproducible | Documented schedule/repetition rule and observations sufficient to distinguish chance/setup. | One failing run. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
