# Verification and claim evidence for Bug Reproduction

Select evidence that can discriminate the claimed property of the bug
reproducer. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Same bug reproduced | Reduced case exhibits defining signature and control/sanity checks distinguish alternatives. | Any failure. |
| Dependency is unnecessary | Case still reproduces after removal in a fresh run. | Source search suggests unused. |
| Reproducer is self-contained | Fresh checkout/copy setup and run succeeds to the target failure with declared prerequisites. | Works on author's existing machine. |
| Sanitization preserved defect | Same internal condition/signature under synthetic data. | Data looks similar. |
| Race is reproducible | Documented schedule/repetition rule and observations sufficient to distinguish chance/setup. | One failing run. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the bug reproducer, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
