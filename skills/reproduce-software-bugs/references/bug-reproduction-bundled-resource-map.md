# Bundled resource map for Bug Reproduction

Use this map to locate resources for bug reproducer. Load only the item required
by the current decision. When an example is a native project, preserve its
manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/python-delimiter-repro/repro.py` | Python implementation, test, or deterministic helper |
| `assets/python-delimiter-repro/verify.py` | Deterministic verifier/runner; inspect supported arguments and evidence limits before use. |

## Use rules

- Use a script only for its documented bug reproducer transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain bug reproducer templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
