# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

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

- `scripts/` contains executable helpers for the skill workflow. Run a helper
  only with documented arguments and inspect stdout/stderr and exit status.
- `assets/` contains templates, complete example projects, fixtures, and other
  material copied, adapted, or executed as part of the task. Assets are not
  instructions by themselves.
- Deliberately faulty fixtures exist only to demonstrate fault discrimination.
  Never present them as recommended implementation code.
- A compiled or passing bundled example establishes only its own contract in the
  executed environment. It does not prove the target repository or production
  system correct.
