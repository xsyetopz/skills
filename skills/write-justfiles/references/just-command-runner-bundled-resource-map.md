# Bundled resource map for Just Command Runner

Use this map to locate resources for justfile recipe. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/example.just` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `scripts/check_justfiles.py` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |
| `scripts/test_check_justfiles.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented justfile recipe transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain justfile recipe templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
