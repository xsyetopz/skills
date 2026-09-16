# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A child used the requested model/tools | Runtime/config status showing the effective assignment. | The child prompt asking for them. |
| A child task completed | Terminal state plus persisted result and inspected outputs/diff. | Silence, timeout, or a progress message. |
| Parallel edits are safe | Disjoint ownership or isolated workspaces with explicit integration order. | Different child names. |
| A phase gate passes | Every required condition linked to suitable evidence. | Majority of checks or reviewer approval alone. |
| Release is ready | Required integration, packaging, security, operational, and policy evidence for the actual target. | Unit tests alone. |
| A baseline change is integrated | Revised baseline plus repeated affected downstream checks. | A note that future work should account for it. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
