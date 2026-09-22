# Performance fixture and tool map for Typescript Runtime Performance

Use this map to locate resources for TypeScript optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/comparisons/pairs.test.ts` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/examples/comparisons/pairs.ts` | TypeScript implementation or fixture |
| `assets/examples/comparisons/runner.ts` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/examples/correctness/semantics.ts` | TypeScript implementation or fixture |
| `assets/examples/package.json` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/examples/reproduction/repro.ts` | TypeScript implementation or fixture |
| `assets/examples/tsconfig.json` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |

## Use rules

- Use a script only for its documented TypeScript optimization transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain TypeScript optimization templates, fixtures, or complete
  example projects. Preserve required manifests and relative paths when copying
  them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
