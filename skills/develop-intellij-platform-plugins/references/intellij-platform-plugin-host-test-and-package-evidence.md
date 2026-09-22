# Host test and package evidence for Intellij Platform Plugin

Select evidence that can discriminate the claimed property of the IntelliJ
Platform plugin. Run the smallest sufficient check first. Broaden only when
another contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Action registered | Target IDE loads plugin and action appears/executes in intended context. | plugin.xml parses. |
| PSI edit correct | Fixture/host test observes intended document/PSI and undo behavior. | Unit method returns text. |
| Threading safe | Platform test/diagnostics and lifecycle scenario across async completion/disposal. | No exception once. |
| Dumb-mode behavior | Test during indexing or platform-supported dumb-mode fixture. | `DumbAware` marker. |
| Compatibility | Plugin verifier/target IDE runs for declared range. | Compile against newest SDK. |
| Packaging | Built ZIP installs and contains manifest/resources/dependencies. | Gradle task created file. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the IntelliJ Platform plugin, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
