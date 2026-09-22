# Extension fixture and template map for Zed WASM Extension

Use this map to locate resources for Zed extension. Load only the item required
by the current decision. When an example is a native project, preserve its
manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/language-extension-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/language-extension-template/extension.toml` | Native manifest or configuration |
| `assets/language-extension-template/languages/example/config.toml` | Native manifest or configuration |
| `assets/language-extension-template/languages/example/highlights.scm` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/language-extension-template/languages/example/outline.scm` | Skill-local output material or executable fixture; use only with its documented consumer. |
| `assets/lsp-extension-template/Cargo.toml` | Native project/build manifest; preserve with the adjacent example project. |
| `assets/lsp-extension-template/TEMPLATE.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/lsp-extension-template/extension.toml` | Native manifest or configuration |
| `assets/lsp-extension-template/src/lib.rs` | Rust implementation or fixture |

## Use rules

- Use a script only for its documented Zed extension transformation. Inspect
  arguments, stdout, stderr, exit status, and created files.
- Assets contain Zed extension templates, fixtures, or complete example
  projects. Preserve required manifests and relative paths when copying them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
