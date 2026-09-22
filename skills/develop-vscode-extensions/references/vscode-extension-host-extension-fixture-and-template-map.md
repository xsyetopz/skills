# Extension fixture and template map for Vscode Extension Host

Use this map to locate resources for VS Code extension. Load only the item
required by the current decision. When an example is a native project, preserve
its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/extension-template/.gitignore` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/extension-template/.vscodeignore` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/extension-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/extension-template/package.json` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/extension-template/src/extension.ts` | TypeScript implementation or fixture |
| `assets/extension-template/test/extension.test.mjs` | Executable test or fault-discrimination fixture; run with the neighboring project configuration. |
| `assets/extension-template/test-host/index.cjs` | CommonJS module or tool configuration |
| `assets/extension-template/tsconfig.json` | Native project/build manifest; preserve with the adjacent example project. |

## Use rules

- Use a script only for its documented VS Code extension transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain VS Code extension templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
