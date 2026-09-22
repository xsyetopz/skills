# Performance fixture and tool map for Dotnet Csharp Performance

Use this map to locate resources for C#/.NET optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/benchmark-csv/baseline.csv` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/benchmark-csv/candidate.csv` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/examples/benchmarks/Benchmarks.csproj` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/examples/benchmarks/Program.cs` | C# implementation or fixture |
| `assets/examples/benchmarks/runtime-experiments.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/examples/comparisons/OwnershipTests.cs` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/examples/comparisons/Pairs.cs` | C# implementation or fixture |
| `assets/examples/comparisons/Pairs.csproj` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/examples/comparisons/Program.cs` | C# implementation or fixture |
| `assets/examples/correctness/Semantics.cs` | C# implementation or fixture |
| `assets/examples/reproduction/Repro.csproj` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/examples/reproduction/repro.cs` | C# implementation or fixture |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |
| `scripts/compare_benchmarks.py` | Python implementation, test, or deterministic helper |
| `scripts/test_compare_benchmarks.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented C#/.NET optimization transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain C#/.NET optimization templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
