# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Command works | Executed command in recorded environment and inspected result. | Command exists in another project or docs. |
| API example is current | Target source/version and compile/type/runtime check appropriate to claim. | Code fence formatting. |
| Link is valid | Local anchor/path resolution or fetched current official page. | Plausible URL. |
| Platform support is documented | Project support matrix/release config and relevant build/test evidence. | Dependency theoretically supports it. |
| Rendered diagram is valid | Mermaid parser/render or supported syntax check plus semantic comparison. | Fence begins with `mermaid`. |

## Command patterns

```sh
# Use repository-native docs checks first, for example:
markdownlint-cli2 "**/*.md"
# Verify code examples with the language/build commands they claim to use.
# Check local links with the existing repository validator.
```

Do not replace repository configuration with a template merely to make lint
pass.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
