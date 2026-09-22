# Performance fixture and tool map for Swift Target Performance

Use this map to locate resources for Swift optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/Package.swift` | Swift implementation or fixture |
| `assets/examples/comparisons/Sources/Pairs/Pairs.swift` | Swift implementation or fixture |
| `assets/examples/comparisons/Sources/PairsCLI/Main.swift` | Swift implementation or fixture |
| `assets/examples/comparisons/Tests/PairsTests/PairsTests.swift` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/examples/correctness/Semantics.swift` | Swift implementation or fixture |
| `assets/examples/reproduction/Repro.swift` | Swift implementation or fixture |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |

## Use rules

- Use a script only for its documented Swift optimization transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain Swift optimization templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
