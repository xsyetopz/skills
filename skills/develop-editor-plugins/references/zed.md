# Zed extensions

Gotchas for `extension.toml`, Rust/WASM code, language servers, Tree-sitter queries, themes, and
registry publishing. Rules mirror Zed v1.21.0 and `zed_extension_api` 0.7.0 sources. Checkers, all
stdlib-only Python:

- `python3 scripts/check_zed_extension.py EXT_DIR [--registry]` checks the manifest, language
  config, and (with `--registry`) the zed-industries/extensions rules.
- `python3 scripts/check_zed_queries.py LANGUAGE_DIR [--node-types FILE]` checks `*.scm` delimiters,
  capture names, and node names against the grammar's `node-types.json`. A clean run does not prove
  that patterns match; run `tree-sitter query` on sample files.
- `python3 scripts/check_zed_theme.py FILE --schema SCHEMA [--root DIR]` validates a theme or icon
  theme against its published schema.
- `python3 scripts/wasm_api_version.py BUILT.wasm --max 0.7.0` prints the `zed:api-version` the
  build declares.

## Contents

- [Manifest and build](#manifest-and-build)
- [Language servers and other Rust features](#language-servers-and-other-rust-features)
- [Languages and queries](#languages-and-queries)
- [Themes, icons, and snippets](#themes-icons-and-snippets)
- [Publishing](#publishing)
- [Sources](#sources)

## Manifest and build

- Mistake: building against a `zed_extension_api` newer than the target Zed accepts. Fix: Zed
  v1.21.0 accepts API 0.0.1 through 0.7.0; use 0.7.0 or older unless the user targets only dev or
  nightly, and run `wasm_api_version.py --max 0.7.0` on the built `.wasm`. The crate README
  compatibility table lags; `wit.rs` is the authority. [wit.rs][wit-rs], [crate][crate]
- Mistake: renaming the dependency (`zed = { package = ... }`). Fix: keep the name
  `zed_extension_api`, import it as `use zed_extension_api as zed;`, and call
  `zed::register_extension!` exactly once. Without the macro the trait compiles but linking fails
  with "failed to find export of ... init-extension". [dev-docs][dev-docs]
- Mistake: a legacy `extension.json`. Fix: use `extension.toml`; the registry packager rejects the
  old format. [package-extensions.js][registry-package]
- Mistake: Rust code in an extension that only ships grammars, queries, themes, or snippets. Fix:
  omit `lib` and the crate; the registry prerequisites forbid Rust code unless the extension
  provides language servers. [prerequisites][prereq]
- Mistake: table key spelled `language-servers`, or keys the parser does not know. Fix: use the
  names from the manifest source (`language_servers`, `[language_servers.<id>]` where the table key
  is the server ID; `[...].name` is ignored). List `languages`, `themes`, or `icon_themes` by hand
  only for files outside the default folders. [extension_manifest.rs][manifest-rs]
- Mistake: taking `cargo check` or `cargo test` on the host target as proof the extension builds.
  Fix: they skip the component link step; use them for pure logic only and build for `wasm32-wasip2`
  through the dev install. Nix or fenix toolchains need that target added by hand.
  [extension_builder.rs][builder-rs]
- Mistake: `cfg!(target_os = ...)` or `std::env::var` to choose a download or read user state. Fix:
  `zed::current_platform()` and `Worktree::shell_env()`. Reason: the extension runs as WASM, not on
  the host OS. [trait docs][trait-docs]
- Mistake: I/O or downloads in `Extension::new`. Fix: there is no `Result` there and no worktree; do
  the work in the first `language_server_command` call.

## Language servers and other Rust features

- Mistake: bundling a server or debug adapter binary. Fix: resolve in this order: `Worktree::which`,
  the cached path, then a download with `zed::download_file`. `Worktree::which` needs no capability;
  downloads and process spawning are gated by `[[capabilities]]`. [capabilities][caps-docs],
  [capability_granter.rs][granter-rs]
- Mistake: writing slash-command, agent-server, or language-model-provider extensions. Fix: do not
  build them; the docs title slash commands "Removed" and the packager rejects or deprecates the
  others. [slash commands][slash-docs], [agent servers][agent-docs]
- Mistake: more than one MCP server in one extension. Fix: ship one per extension. [MCP
  extensions][mcp-docs]
- Mistake: debug adapter binaries copied into the extension. Fix: locate them on `PATH` or download
  them like a language server. [debugger extensions][dap-docs]

## Languages and queries

- Mistake: a grammar `rev` that is a branch or tag. Fix: pin a 40-character commit SHA and re-run
  `check_zed_queries.py --node-types` whenever it changes; queries written for another revision name
  nodes that no longer exist. [languages][lang-docs]
- Mistake: a language name that differs from the one other extensions use (`Shell Script`,
  `Markdown`). Fix: match names exactly; language servers attach by name. [languages][lang-docs]
- Mistake: query files that do not parse or use capture names Zed does not read. Fix: run
  `check_zed_queries.py`; it checks the captures Zed reads per file. [grammar.rs][grammar-rs]
- Mistake: reusing a grammar from another extension by copying it. Fix: point `[grammars.<name>]` at
  the same repository and rev. [FAQ][faq]

## Themes, icons, and snippets

- Mistake: a theme color not written as `#rgb`, `#rgba`, `#rrggbb`, or `#rrggbbaa`, or a misspelled
  style key. Fix: run `check_zed_theme.py` with the published schema; the schema allows unknown keys
  and Zed drops misspelled ones. The packager also rejects the deprecated
  `scrollbar_thumb.background`. [theme schema][theme-schema], [themes][theme-docs]
- Mistake: an icon theme that names a missing file or an undefined `file_icons` key. Fix: run the
  checker with `--root` set to the extension root. [icon schema][icon-schema], [icon
  themes][icon-docs]
- Mistake: bundling themes and icon themes with code in one extension. Fix: keep them in their own
  extensions.
- Mistake: snippets that are not listed or use the wrong file name. Fix: list them under `snippets`
  in `extension.toml`. [snippets][snippet-docs]

## Publishing

- Mistake: a missing or unaccepted license file. Fix: include one of the accepted licenses at the
  extension root. [license requirements][license], [license.js][license-js]
- Mistake: editing the registry without being asked. Fix: stop after
  `check_zed_extension.py --registry`; open or update a registry PR only when the user asks, and
  sort entries with `pnpm sort-extensions` there (the registry's own tool), never npm or bun.
  [registry][registry], [publishing guide][guide]
- Mistake: reporting an in-editor step as done after a passing build or checker. Fix: say "Not
  runnable here" unless Zed ran it.

## Sources

[agent-docs]: https://zed.dev/docs/extensions/agent-servers
[builder-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_builder.rs
[caps-docs]: https://zed.dev/docs/extensions/capabilities
[crate]: https://crates.io/crates/zed_extension_api
[dap-docs]: https://zed.dev/docs/extensions/debugger-extensions
[dev-docs]: https://zed.dev/docs/extensions/developing-extensions
[faq]: https://zed.dev/docs/extensions/publishing/faq#grammar-reuse
[grammar-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/language_core/src/grammar.rs
[granter-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_host/src/capability_granter.rs
[guide]: https://zed.dev/docs/extensions/publishing/publishing-guide
[icon-docs]: https://zed.dev/docs/extensions/icon-themes
[icon-schema]: https://zed.dev/schema/icon_themes/v0.3.0.json
[lang-docs]: https://zed.dev/docs/extensions/languages
[license]: https://zed.dev/docs/extensions/publishing/license-requirements
[license-js]: https://github.com/zed-industries/extensions/blob/main/src/lib/license.js
[manifest-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_manifest.rs
[mcp-docs]: https://zed.dev/docs/extensions/mcp-extensions
[prereq]: https://zed.dev/docs/extensions/publishing/prerequisites
[registry]: https://github.com/zed-industries/extensions
[registry-package]: https://github.com/zed-industries/extensions/blob/main/src/package-extensions.js
[slash-docs]: https://github.com/zed-industries/zed/blob/v1.21.0/docs/src/extensions/slash-commands.md
[snippet-docs]: https://zed.dev/docs/extensions/snippets
[theme-docs]: https://zed.dev/docs/extensions/themes
[theme-schema]: https://zed.dev/schema/themes/v0.2.0.json
[trait-docs]: https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/trait.Extension.html
[wit-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_host/src/wasm_host/wit.rs
