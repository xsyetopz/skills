# Bundled resource map for Agent Hook

Use this map to locate resources for agent hook. Load only the item required by
the current decision. When an example is a native project, preserve its
manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/claude-code/settings.json` | Native manifest, configuration, or structured fixture |
| `assets/codex/hooks.json` | Native manifest, configuration, or structured fixture |
| `assets/cursor/hooks.json` | Native manifest, configuration, or structured fixture |
| `assets/fixtures/claude-code.json` | Native manifest, configuration, or structured fixture |
| `assets/fixtures/codex.json` | Native manifest, configuration, or structured fixture |
| `assets/fixtures/cursor.json` | Native manifest, configuration, or structured fixture |
| `assets/fixtures/gemini-cli.json` | Native manifest, configuration, or structured fixture |
| `assets/fixtures/github-copilot.json` | Native manifest, configuration, or structured fixture |
| `assets/fixtures/vscode.json` | Native manifest, configuration, or structured fixture |
| `assets/gemini-cli/settings.json` | Native manifest, configuration, or structured fixture |
| `assets/github-copilot/hooks.json` | Native manifest, configuration, or structured fixture |
| `assets/opencode/index.ts` | TypeScript implementation or fixture |
| `assets/opencode-v1/observe.ts` | TypeScript implementation or fixture |
| `assets/shared/observe.py` | Python implementation, test, or deterministic helper |
| `assets/vscode/hooks.json` | Native manifest, configuration, or structured fixture |
| `scripts/test_assets.py` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |

## Use rules

- Use a script only for its documented agent hook transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain agent hook templates, fixtures, or complete example projects.
  Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
