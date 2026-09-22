# Performance fixture and tool map for Python Interpreter Performance

Use this map to locate resources for Python optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/benchmarks/bench_pyperf.py` | Python implementation, test, or deterministic helper |
| `assets/examples/comparisons/pairs.py` | Python implementation, test, or deterministic helper |
| `assets/examples/comparisons/test_pairs.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/examples/correctness/semantics.py` | Python implementation, test, or deterministic helper |
| `assets/examples/pyproject.toml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/examples/pyrightconfig.json` | Native manifest, configuration, or structured fixture |
| `assets/examples/reproduction/repro.py` | Python implementation, test, or deterministic helper |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |

## Use rules

- Use a script only for its documented Python optimization transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain Python optimization templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
