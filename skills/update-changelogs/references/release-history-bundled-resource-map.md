# Bundled resource map for Release History

Use this map to locate resources for changelog entry. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `scripts/audit_changelog.py` | Python implementation, test, or deterministic helper |
| `scripts/audit_semver.py` | Python implementation, test, or deterministic helper |
| `scripts/changelog_markdown.py` | Python implementation, test, or deterministic helper |
| `scripts/test_validators.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/CHANGELOG.template.md` | Output template; adapt to the repository format and verified revision range. |

## Use rules

- Use a script only for its documented changelog entry transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain changelog entry templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
