# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command works | Actual extension-host invocation and user-visible result. | Manifest string/unit test alone. |
| Stale result is suppressed | Host/integration test changes document/request before completion and observes no stale edit. | Generation variable exists. |
| Remote/web support | Test in declared host or target-specific automated harness. | Local desktop test. |
| Trust boundary enforced | Untrusted workspace attempt is denied/limited by host-aware logic. | Command hidden from palette. |
| Package is valid | VSIX build, content inspection, installation/launch on target VS Code. | `npm run compile`. |
| Resources clean up | Deactivate/dispose/reload test with no duplicate registration/process/watchers. | No exception during one activation. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
