# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Action registered | Target IDE loads plugin and action appears/executes in intended context. | plugin.xml parses. |
| PSI edit correct | Fixture/host test observes intended document/PSI and undo behavior. | Unit method returns text. |
| Threading safe | Platform test/diagnostics and lifecycle scenario across async completion/disposal. | No exception once. |
| Dumb-mode behavior | Test during indexing or platform-supported dumb-mode fixture. | `DumbAware` marker. |
| Compatibility | Plugin verifier/target IDE runs for declared range. | Compile against newest SDK. |
| Packaging | Built ZIP installs and contains manifest/resources/dependencies. | Gradle task created file. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
