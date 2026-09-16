# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

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

- `scripts/` contains executable helpers for the skill workflow. Run a helper
  only with documented arguments and inspect stdout/stderr and exit status.
- `assets/` contains templates, complete example projects, fixtures, and other
  material copied, adapted, or executed as part of the task. Assets are not
  instructions by themselves.
- Deliberately faulty fixtures exist only to demonstrate fault discrimination.
  Never present them as recommended implementation code.
- A compiled or passing bundled example establishes only its own contract in the
  executed environment. It does not prove the target repository or production
  system correct.
