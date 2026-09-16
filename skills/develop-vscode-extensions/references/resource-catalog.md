# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

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
