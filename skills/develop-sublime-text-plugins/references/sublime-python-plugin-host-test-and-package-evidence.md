# Host test and package evidence for Sublime Python Plugin

Select evidence that can discriminate the claimed property of the Sublime Text
plugin. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command works | Sublime host invocation and observed view/buffer result/undo. | Stub unit test. |
| Async result fresh | Host test changes/closes view before completion and observes no stale edit. | View ID captured. |
| Runtime compatible | Syntax/import/test under embedded Python and target build. | Newest system Python. |
| Reload clean | Repeated reload/unload with no duplicate callbacks/processes. | One start. |
| Resource loads | Clean package install and `load_resource`/asset behavior. | File exists in source. |
| Package valid | Archive content and host install/command execution. | Zip created. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the Sublime Text plugin, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
