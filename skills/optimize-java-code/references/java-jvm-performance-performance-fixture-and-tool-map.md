# Performance fixture and tool map for Java JVM Performance

Use this map to locate resources for Java/JVM optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/benchmarks/pom.xml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/examples/benchmarks/src/main/java/example/DelimiterBench.java` | Java implementation or fixture |
| `assets/examples/comparisons/Pairs.java` | Java implementation or fixture |
| `assets/examples/correctness/Semantics.java` | Java implementation or fixture |
| `assets/examples/reproduction/Repro.java` | Java implementation or fixture |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |

## Use rules

- Use a script only for its documented Java/JVM optimization transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain Java/JVM optimization templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
