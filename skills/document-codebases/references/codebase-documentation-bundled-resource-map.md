# Bundled resource map for Codebase Documentation

Use this map to locate resources for codebase documentation. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/.markdownlint-cli2.jsonc` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/CONTRIBUTING.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/repository-overview.template.md` | Output template; copy and adapt without treating placeholders as facts. |

## Use rules

- Use a script only for its documented codebase documentation transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain codebase documentation templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
