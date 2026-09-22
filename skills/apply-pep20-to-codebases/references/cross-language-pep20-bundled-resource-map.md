# Bundled resource map for Cross Language PEP 20

Use this map to locate resources for cross-language design review. Load only the
item required by the current decision. When an example is a native project,
preserve its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/examples/explicit_behavior.py` | Python implementation, test, or deterministic helper |
| `scripts/test_examples.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented cross-language design review
  transformation. Inspect arguments, stdout, stderr, exit status, and created
  files.
- Assets contain cross-language design review templates, fixtures, or complete
  example projects. Preserve required manifests and relative paths when copying
  them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
