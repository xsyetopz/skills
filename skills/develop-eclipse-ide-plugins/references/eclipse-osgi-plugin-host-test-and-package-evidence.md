# Host test and package evidence for Eclipse OSGi Plugin

Select evidence that can discriminate the claimed property of the Eclipse
plugin. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Extension registered | Target IDE loads and invokes extension point. | plugin.xml contains element. |
| Job behavior correct | PDE/host test observes cancellation, scheduling, progress, and UI handoff. | Job class compiles. |
| Resource lifecycle safe | Open/close/reload scenario with disposal/no duplicate listeners. | No immediate exception. |
| Target compatibility | Tycho/PDE build and tests using declared target platform. | Local Eclipse version. |
| p2 install works | Clean install/resolution/start from produced repository. | Repository files exist. |
| Workspace mutation safe | Concurrent/resource test under scheduling rule. | Synchronized Java block alone. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the Eclipse plugin, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
