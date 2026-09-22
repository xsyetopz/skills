# Host test and package evidence for Vscode Extension Host

Select evidence that can discriminate the claimed property of the VS Code
extension. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command works | Actual extension-host invocation and user-visible result. | Manifest string/unit test alone. |
| Stale result is suppressed | Host/integration test changes document/request before completion and observes no stale edit. | Generation variable exists. |
| Remote/web support | Test in declared host or target-specific automated harness. | Local desktop test. |
| Trust boundary enforced | Untrusted workspace attempt is denied/limited by host-aware logic. | Command hidden from palette. |
| Package is valid | VSIX build, content inspection, installation/launch on target VS Code. | `npm run compile`. |
| Resources clean up | Deactivate/dispose/reload test with no duplicate registration/process/watchers. | No exception during one activation. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the VS Code extension, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
