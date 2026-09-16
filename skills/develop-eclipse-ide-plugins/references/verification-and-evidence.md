# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Extension registered | Target IDE loads and invokes extension point. | plugin.xml contains element. |
| Job behavior correct | PDE/host test observes cancellation, scheduling, progress, and UI handoff. | Job class compiles. |
| Resource lifecycle safe | Open/close/reload scenario with disposal/no duplicate listeners. | No immediate exception. |
| Target compatibility | Tycho/PDE build and tests using declared target platform. | Local Eclipse version. |
| p2 install works | Clean install/resolution/start from produced repository. | Repository files exist. |
| Workspace mutation safe | Concurrent/resource test under scheduling rule. | Synchronized Java block alone. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
