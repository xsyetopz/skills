# Bundled resource map for Agent Skill

Use this map to locate resources for Agent Skill package. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/SKILL.template.md` | Output template; copy and adapt without treating placeholders as facts. |

## Use rules

- Use a script only for its documented Agent Skill package transformation.
  Inspect arguments, stdout, stderr, exit status, and created files.
- Assets contain Agent Skill package templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
