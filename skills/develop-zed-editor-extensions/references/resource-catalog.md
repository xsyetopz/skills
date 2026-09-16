# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not load every source file into context by default. Preserve complete native
project directories—including manifests, locks, descriptors, and fixtures—when
copying or executing an example.

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
