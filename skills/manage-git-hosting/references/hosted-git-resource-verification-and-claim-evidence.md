# Verification and claim evidence for Hosted Git Resource

Select evidence that can discriminate the claimed property of the hosted Git
operation. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Comment/label/state changed | Read-back resource contains exact requested change once. | Successful HTTP/CLI exit only. |
| Review submitted | Provider review object with intended state and commit/head context. | Comment text saying “approved”. |
| Merge completed | PR/MR merged state and resulting commit/ref under required rules. | Merge command accepted before checks finish. |
| Release published | Release object state, tag/commit identity, assets/digests, and public availability. | Draft body exists. |
| Access/settings changed | Effective provider setting/member permission and relevant audit/protection result. | Request payload echoed. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the hosted Git operation, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
