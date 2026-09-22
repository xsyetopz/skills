# Verification and claim evidence for Phase Gated Delivery

Select evidence that can discriminate the claimed property of the multi-agent
phase coordination. Run the smallest sufficient check first. Broaden only when
another contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A child used the requested model/tools | Runtime/config status showing the effective assignment. | The child prompt asking for them. |
| A child task completed | Terminal state plus persisted result and inspected outputs/diff. | Silence, timeout, or a progress message. |
| Parallel edits are safe | Disjoint ownership or isolated workspaces with explicit integration order. | Different child names. |
| A phase gate passes | Every required condition linked to suitable evidence. | Majority of checks or reviewer approval alone. |
| Release is ready | Required integration, packaging, security, operational, and policy evidence for the actual target. | Unit tests alone. |
| A baseline change is integrated | Revised baseline plus repeated affected downstream checks. | A note that future work should account for it. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the multi-agent phase coordination, separate authored checks, executed
checks, static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
