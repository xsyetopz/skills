# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Comment/label/state changed | Read-back resource contains exact requested change once. | Successful HTTP/CLI exit only. |
| Review submitted | Provider review object with intended state and commit/head context. | Comment text saying “approved”. |
| Merge completed | PR/MR merged state and resulting commit/ref under required rules. | Merge command accepted before checks finish. |
| Release published | Release object state, tag/commit identity, assets/digests, and public availability. | Draft body exists. |
| Access/settings changed | Effective provider setting/member permission and relevant audit/protection result. | Request payload echoed. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
