# Verification and claim evidence for Codebase Documentation

Select evidence that can discriminate the claimed property of the codebase
documentation. Run the smallest sufficient check first. Broaden only when
another contract boundary changed.

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

For the codebase documentation, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
