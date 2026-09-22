# Performance fixture and tool map for Rust Native Performance

Use this map to locate resources for Rust optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/Cargo.lock` | Dependency lock/reproducibility artifact; preserve with the adjacent project and do not regenerate without need. |
| `assets/examples/Cargo.toml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/examples/comparisons/src/lib.rs` | Rust implementation or fixture |
| `assets/examples/comparisons/src/main.rs` | Rust implementation or fixture |
| `assets/examples/comparisons/tests/pairs.rs` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/examples/correctness/semantics.rs` | Rust implementation or fixture |
| `assets/examples/reproduction/repro.rs` | Rust implementation or fixture |
| `assets/examples/rust-toolchain.toml` | Native manifest or configuration |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |

## Use rules

- Use a script only for its documented Rust optimization transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain Rust optimization templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
