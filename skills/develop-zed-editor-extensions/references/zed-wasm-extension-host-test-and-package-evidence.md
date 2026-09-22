# Host test and package evidence for Zed WASM Extension

Select evidence that can discriminate the claimed property of the Zed extension.
Run the smallest sufficient check first. Broaden only when another contract
boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Extension recognized | Selected Zed version loads manifest/extension and exposes intended language/server. | TOML parses. |
| Queries correct | Representative fixtures produce expected captures/indent/outline on selected grammar. | Query file exists. |
| Wasm API compatible | Build with target SDK/toolchain and run in selected host. | Rust compile outside host. |
| Server starts correctly | Resolved binary/version/args/env and real protocol initialization in Zed. | Executable path found. |
| Download safe | Expected platform asset, digest/signature where available, and controlled cache/permissions. | HTTP 200. |
| Registry package valid | Clean install and activation from packaged/published form. | Local source load only. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the Zed extension, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
