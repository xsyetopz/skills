# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Extension recognized | Selected Zed version loads manifest/extension and exposes intended language/server. | TOML parses. |
| Queries correct | Representative fixtures produce expected captures/indent/outline on selected grammar. | Query file exists. |
| Wasm API compatible | Build with target SDK/toolchain and run in selected host. | Rust compile outside host. |
| Server starts correctly | Resolved binary/version/args/env and real protocol initialization in Zed. | Executable path found. |
| Download safe | Expected platform asset, digest/signature where available, and controlled cache/permissions. | HTTP 200. |
| Registry package valid | Clean install and activation from packaged/published form. | Local source load only. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
