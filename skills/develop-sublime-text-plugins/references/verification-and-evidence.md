# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command works | Sublime host invocation and observed view/buffer result/undo. | Stub unit test. |
| Async result fresh | Host test changes/closes view before completion and observes no stale edit. | View ID captured. |
| Runtime compatible | Syntax/import/test under embedded Python and target build. | Newest system Python. |
| Reload clean | Repeated reload/unload with no duplicate callbacks/processes. | One start. |
| Resource loads | Clean package install and `load_resource`/asset behavior. | File exists in source. |
| Package valid | Archive content and host install/command execution. | Zip created. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
