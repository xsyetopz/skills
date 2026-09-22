# Performance fixture and tool map for Cpp Native Performance

Use this map to locate resources for C++ optimization. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/benchmarks/CMakeLists.txt` | Text fixture or native metadata |
| `assets/examples/benchmarks/delimiter_bench.cpp` | C++ implementation or fixture |
| `assets/examples/comparisons/cpp_pairs.cpp` | C++ implementation or fixture |
| `assets/examples/comparisons/justfile` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/examples/comparisons/xmake.lua` | Lua implementation or fixture |
| `assets/examples/correctness/semantics.cpp` | C++ implementation or fixture |
| `assets/examples/reproduction/repro.cpp` | C++ implementation or fixture |
| `assets/examples/verify.sh` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `assets/performance-report.md` | Output template, worked example, or agent-readable fixture |

## Use rules

- Use a script only for its documented C++ optimization transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain C++ optimization templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
