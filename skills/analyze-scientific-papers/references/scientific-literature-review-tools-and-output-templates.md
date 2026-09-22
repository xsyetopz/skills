# Review tools and output templates for Scientific Literature

Use this map to locate resources for paper synthesis. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/evidence-note-template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/metadata-fixtures/arxiv.atom` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/metadata-fixtures/crossref.json` | Native manifest, configuration, or structured fixture |
| `assets/metadata-fixtures/openalex.json` | Native manifest, configuration, or structured fixture |
| `scripts/fetch_metadata.py` | Python implementation, test, or deterministic helper |
| `scripts/test_fetch_metadata.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented paper synthesis transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain paper synthesis templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
