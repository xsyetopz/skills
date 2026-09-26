---
name: develop-zed-editor-extensions
description: >-
  Builds and publishes Zed editor extensions: extension.toml, Rust/WASM code,
  language servers, Tree-sitter queries, themes, snippets, MCP servers, debug
  adapters. Use when writing or fixing a Zed extension. Not for Zed user
  settings.
---

# Develop Zed Editor Extensions

Build or change a Zed extension. Each card in the references is checked
against Zed v1.21.0, `zed_extension_api` 0.7.0, the Zed docs, and the
registry's CI code, and gives the definition, **Use when** and **Do not
use when** conditions, the cost it removes, and verification. Example
extensions under `assets/examples/` cover every runnable card: a Makefile
language, a Marksman LSP, an MCP server, an lldb-dap debugger, a theme,
and an icon theme.

## Workflow

1. Classify the request with the [route table](#route-the-task-to-a-card)
   and decide whether the extension needs Rust: only language servers,
   MCP servers, and debuggers do ([extension crate][crate]).
1. Read the existing `extension.toml`, `Cargo.toml`, `Cargo.lock`,
   `languages/*/config.toml`, and CI files. Record the pinned
   `zed_extension_api` and the oldest Zed version the user supports.
   Check them against the [API range][api].
1. Write or change only the files the cards name. For a language, also
   pin the grammar `rev` to a commit SHA ([grammar][grammar]). For a
   server, also resolve `which` first, then the cache, then the
   download ([server command][lsc]).
1. Build with the toolchain that owns the target ([toolchain][tc]):
   `cargo build --release --target wasm32-wasip2`. Then run
   `python3 scripts/wasm_api_version.py <crate>.wasm --max 0.7.0`.
1. Run the checkers from the skill directory:
   `python3 scripts/check_extension.py EXT [--registry]`,
   `python3 scripts/check_queries.py EXT/languages/NAME --node-types
   GRAMMAR/src/node-types.json`, and
   `python3 scripts/check_theme.py FILE --schema SCHEMA [--root EXT]`.
1. Compile the queries on a sample file:
   `tree-sitter query -p GRAMMAR_DIR QUERY SAMPLE` ([query
   check][qcheck]).
1. Hand the user the in-editor steps: `zed: install dev extension`,
   then read `Zed.log` or run `zed --foreground` ([dev install][dev]).
1. For publication, follow [publishing](references/publishing.md). Open
   the registry PR only when the user asks for it.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| New extension, manifest fields | [Extension manifest](references/manifest-and-build.md#extension-manifest) |
| Feature silently missing, no log error | [Ignored manifest keys](references/manifest-and-build.md#ignored-manifest-keys) |
| Rust needed? `crate-type`, dependency pin | [Extension crate](references/manifest-and-build.md#extension-crate) |
| Works on nightly, not on stable; version choice | [API version](references/manifest-and-build.md#api-version-and-zed-compatibility) |
| `failed to find export of function init-extension` | [register\_extension](references/manifest-and-build.md#register_extension-and-extensionnew) |
| `can't find crate for core` with target installed | [Toolchain](references/manifest-and-build.md#toolchain-that-owns-the-target) |
| Build or clippy for the wasm target | [Build for wasm32-wasip2](references/manifest-and-build.md#build-for-wasm32-wasip2) |
| Extension must run a host tool | [Process capability](references/manifest-and-build.md#process-execution-capability) |
| Try it in Zed, read logs | [Dev extension install](references/manifest-and-build.md#dev-extension-install) |
| Attach a server to a language | [Server registration](references/language-servers.md#language-server-registration), [command](references/language-servers.md#language_server_command) |
| Prefer the user's installed server | [Worktree::which](references/language-servers.md#worktreewhich) |
| Read user environment variables | [Worktree::shell\_env](references/language-servers.md#worktreeshell_env) |
| Download a server from GitHub releases | [Latest release](references/language-servers.md#latest-release-and-platform-asset), [pinned release](references/language-servers.md#pinned-github-release) |
| Archive types, `.tar.gz`, `.zip`, `.gz` | [download\_file](references/language-servers.md#download_file-and-archive-types) |
| "permission denied" at server start | [make\_file\_executable](references/language-servers.md#make_file_executable) |
| Network call on every start, many versions on disk | [Download cache](references/language-servers.md#version-scoped-download-cache) |
| Show progress or failure for a server | [Installation status](references/language-servers.md#installation-status) |
| User set `lsp.<id>.binary` | [User binary settings](references/language-servers.md#user-binary-settings-take-precedence) |
| Pass settings to the server | [Init options and configuration](references/language-servers.md#server-options-and-configuration) |
| Server published on npm | [npm servers](references/language-servers.md#npm-distributed-servers) |
| New language, `config.toml` | [Language config](references/languages-and-queries.md#language-directory-and-configtoml) |
| Files open as Plain Text | [File matching](references/languages-and-queries.md#file-matching) |
| Add or update a grammar | [Grammar](references/languages-and-queries.md#grammar-with-a-pinned-revision), [local grammar](references/languages-and-queries.md#local-grammar-during-development) |
| Colors, brackets, outline, indentation | [highlights](references/languages-and-queries.md#highlightsscm), [fallbacks](references/languages-and-queries.md#fallback-highlight-captures), [brackets](references/languages-and-queries.md#bracketsscm), [outline](references/languages-and-queries.md#outlinescm), [indents](references/languages-and-queries.md#indentsscm) |
| Embedded language, scoped settings | [injections](references/languages-and-queries.md#injectionsscm), [overrides](references/languages-and-queries.md#overridesscm-and-scoped-settings) |
| Vim text objects, redaction, run buttons | [textobjects](references/languages-and-queries.md#textobjectsscm), [redactions](references/languages-and-queries.md#redactionsscm), [runnables](references/languages-and-queries.md#runnablesscm-and-tasksjson) |
| Query errors, grammar drift | [Query check](references/languages-and-queries.md#query-check) |
| Theme, colors, syntax styles | [Theme file](references/themes-icons-snippets.md#theme-family-file), [syntax](references/themes-icons-snippets.md#syntax-styles), [colors](references/themes-icons-snippets.md#theme-colors) |
| Icon theme, missing icons | [Icon theme](references/themes-icons-snippets.md#icon-theme-file), [icon lookup](references/themes-icons-snippets.md#icon-lookup-and-fallback) |
| Snippets | [Snippets](references/themes-icons-snippets.md#snippets) |
| MCP server for the Agent Panel | [Context server](references/mcp-and-debuggers.md#context-server-registration), [configuration](references/mcp-and-debuggers.md#context_server_configuration), [settings](references/mcp-and-debuggers.md#context-server-settings) |
| "Add a slash command" or agent server | [Removed kinds](references/mcp-and-debuggers.md#removed-extension-kinds) |
| Debug adapter | [Registration](references/mcp-and-debuggers.md#debug-adapter-registration), [get\_dap\_binary](references/mcp-and-debuggers.md#get_dap_binary), [request kind](references/mcp-and-debuggers.md#dap_request_kind), [UI config](references/mcp-and-debuggers.md#dap_config_to_scenario) |
| Debug a build task | [Debug locators](references/mcp-and-debuggers.md#debug-locators) |
| Registry naming, license, PR, update | [ID rules](references/publishing.md#extension-id-and-category-rules), [license](references/publishing.md#license-at-the-extension-root), [CI](references/publishing.md#registry-ci-checks), [PR](references/publishing.md#submission-pr), [subdirectory](references/publishing.md#extension-in-a-subdirectory), [update](references/publishing.md#update-pr) |

## Rules

- Use `zed_extension_api` 0.7.0 or older unless the user targets only
  Zed dev or nightly. Stable v1.21.0 accepts API 0.0.1 through 0.7.0.
  Check the built `.wasm` with `wasm_api_version.py --max 0.7.0`.
- Keep the dependency name `zed_extension_api`. Import it with
  `use zed_extension_api as zed;`, and call
  `zed::register_extension!` exactly once.
- Do not branch on `cfg!(target_os)` or read `std::env::var` for user
  state. Use `zed::current_platform()` and `Worktree::shell_env()`.
- Resolve servers in this order: `Worktree::which`, the cached path,
  then the download. Never bundle a server or debug adapter binary.
- Pin every grammar `rev` to a 40-character commit SHA. Re-run the
  query check whenever `rev` changes.
- Use the table names from the manifest source (`language_servers`,
  not `language-servers`). Match language names exactly (`Markdown`,
  `Shell Script`).
- Keep themes and icon themes in their own extensions. Ship at most one
  MCP server per extension.
- Do not build slash-command, agent-server, or language-model-provider
  extensions. They are removed, deprecated, or rejected by the
  packager.
- Report every in-editor step as Not runnable here unless Zed ran it.
  A passing `cargo build` or checker does not prove editor behavior.
- Do not open, push, or update a registry PR unless the user asks for
  it. Use `pnpm sort-extensions` there, never npm or bun.

## Bundled tools

- `scripts/check_extension.py EXT [--registry] [--json]` checks
  `extension.toml`, `Cargo.toml`, languages, snippets, debug schemas,
  capabilities, and, with `--registry`, the ID, name, description,
  license, and feature mix. Exit status: 0 clean, 1 errors, 2 usage.
- `scripts/check_queries.py LANG_DIR [--node-types FILE]` checks
  delimiters, per-file captures, and node and field names.
- `scripts/check_theme.py FILE --schema SCHEMA [--root EXT]` checks
  the theme or icon theme against the schema, colors, icon files, and
  icon keys.
- `scripts/wasm_api_version.py FILE.wasm [--max X.Y.Z]` reads
  `zed:api-version`.
- `sh assets/examples/verify.sh fetch` needs the network: it fetches
  Cargo dependencies, the pinned grammar, and the schemas.
  `sh assets/examples/verify.sh` then runs offline. `TREE_SITTER`
  adds the query compile step.

Each script has a standard-library `test_*.py` next to it.

## References

- [Manifest, crate, and build](references/manifest-and-build.md)
- [Language servers](references/language-servers.md)
- [Languages, grammars, and queries](references/languages-and-queries.md)
- [Themes, icon themes, and snippets](references/themes-icons-snippets.md)
- [MCP servers and debuggers](references/mcp-and-debuggers.md)
- [Publishing to the registry](references/publishing.md)

## Completion evidence

The final report contains:

- The files changed and the cards applied.
- The `zed_extension_api` requirement and the `wasm_api_version.py`
  output for each crate.
- The `cargo build --release --target wasm32-wasip2` result, and the
  `cargo test` and `clippy` results where a crate exists.
- The checker summary lines (`N errors, M warnings`), with each
  remaining warning explained.
- `tree-sitter query` capture counts for each query file on a sample,
  or the exact reason the CLI was unavailable.
- The in-editor steps for the user, marked Not runnable here unless
  Zed ran them. Registry steps are listed as pending until the user
  approves them.

[crate]: references/manifest-and-build.md#extension-crate
[api]: references/manifest-and-build.md#api-version-and-zed-compatibility
[tc]: references/manifest-and-build.md#toolchain-that-owns-the-target
[dev]: references/manifest-and-build.md#dev-extension-install
[lsc]: references/language-servers.md#language_server_command
[grammar]: references/languages-and-queries.md#grammar-with-a-pinned-revision
[qcheck]: references/languages-and-queries.md#query-check
