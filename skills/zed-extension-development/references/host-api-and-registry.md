# Zed manifest, WASM host and registry

Research: 2026-09-12. Stable host examined: **Zed 1.19.2**
([release](https://github.com/zed-industries/zed/releases/tag/v1.19.2));
published extension crate baseline **zed_extension_api 0.7.0**
([crate](https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/)). The host
source's 0.8.0 crate has `publish=false`, so it is not a crates.io stable
default.

## Manifest and declarative capabilities

```toml
id = "example-language"
name = "Example Language"
version = "0.1.0"
schema_version = 1
authors = ["Example Maintainer"]
description = "Language support for Example"
repository = "https://github.com/example/example-language"

[language_servers.example-lsp]
name = "Example LSP"
languages = ["Example"]
```

Replace the repository URL. Keep language display names, server IDs and grammar
IDs aligned. Themes, icon themes, snippets and language queries can be
declarative; procedural server/debugger hooks use the supported Rust interface.
Extensions cannot assume arbitrary editor UI/event APIs.
[Development contract](https://zed.dev/docs/extensions/developing-extensions).

For a procedural extension, Cargo uses `[lib] crate-type=["cdylib"]` and a
compatible pinned `zed_extension_api`. Current builds use `wasm32-wasip2`; Zed
can install it when Rust comes through rustup. Grammar compilation additionally
needs wasi-sdk, downloaded by the host or supplied through `WASI_SDK_PATH`.
`cargo build --release --target wasm32-wasip2` verifies Rust/WASM compilation,
not manifest/query or host behavior. [Host source compatibility][source-0-1].

[source-0-1]:
  https://github.com/zed-industries/zed/blob/v1.19.2/crates/extension_api/README.md

## User-installed server implementation

Use the [LSP starter](../assets/lsp-extension-template/TEMPLATE.md) for a
user-installed server. It returns an executable found by `Worktree::which`,
server-specific arguments and only extension-specific environment overrides. It
does not implement managed downloads.

Replace the executable placeholder and arguments with the actual server
interface. Worktree APIs resolve runtime environment, while Rust `cfg` describes
the WASM compilation target. `current_platform()` supplies host OS/architecture.
Return command data for the host to launch; do not assume `std::process`/native
filesystem behavior. Return protocol JSON from initialization-option and
workspace-configuration hooks. Do not double-serialize values.

In Zed 1.19.2, the host resolves an explicit `lsp.<id>.binary.path` before
calling the adapter. It also applies configured argument and environment
overrides and merges the worktree shell environment. Do not duplicate that
policy inside the extension or overwrite user settings with defaults. A custom
binary path with no configured arguments uses an empty argument list rather than
the adapter defaults, so document required server arguments. [Host resolution
order][host-resolution].

[host-resolution]:
  https://github.com/zed-industries/zed/blob/v1.19.2/crates/project/src/lsp_store.rs

[Published API][source-1-1].

[source-1-1]:
  https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/trait.Extension.html

## Managed binaries and lifecycle

If downloads are requested, resolve user-configured/system binaries first.
Otherwise select an immutable release asset by host OS/architecture, download
with `download_file` and the matching archive type, extract into extension-owned
storage and apply executable permissions with the supported API. Report
installation status through `set_language_server_installation_status`. Cache the
resolved version/path only while it remains valid; a half-extracted file must
not count as installed. Classify missing asset, download, extraction,
permissions and launch failures separately.
[API functions](https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/).

The host owns worktrees, documents and server process sessions. Avoid keeping
stale handles across unrelated callbacks; keep portable version/configuration
state separate from host resources. Do not run broad filesystem searches or a
download on every completion/label callback. Preserve user-selected binaries
even if a managed version is newer.

## Debug, package and publish

Install locally through `zed: install dev extension`, selecting the manifest
directory. It overrides an installed published version; use a development
profile. The verified 1.19.2 CLI supports `--user-data-dir DIR` for an isolated
host data directory; verify the target version rather than inventing a profile
flag. Inspect `zed: open log` and launch `zed --foreground` for extension
stdout/stderr. Test a real file for grammar, server activation, configuration
and shutdown. A successful native `cargo check` does not verify the WASM
interface.

Keep manifest version, Cargo version, registry record, repository revision and
upstream tool version distinct. Publish through the registry:

1. Fork/clone `zed-industries/extensions` and initialize its submodules.
2. Add the public extension repository with an HTTPS submodule URL under
   `extensions/ID`; select a commit reachable from a branch.
3. Add `[ID]`, `submodule = "extensions/ID"` and matching `version` to root
   `extensions.toml`. For a monorepo, add `path = "packages/zed"` for the
   extension subdirectory.
4. Run the registry's `bun run sort-extensions`, review the gitlink and
   metadata, and submit one extension per PR. Merge triggers
   packaging/publication. Updates change the gitlink and matching
   registry/manifest version.

The current queue permits at most three open PRs per author and closes
submissions without a response to feedback for three weeks. [Publishing
procedure][source-3-1],
[updates](https://zed.dev/docs/extensions/publishing/updating-and-maintenance).

Place an accepted license at the extension root, including when that root is a
repository subdirectory. Accepted licenses on the research date are Apache-2.0,
BSD-2-Clause, BSD-3-Clause, CC-BY-4.0, GPLv3, LGPLv3, MIT, Unlicense and zlib;
this requirement applies to extension code, not automatically to downloaded
tools. Do not relicense an existing project without authority. [License
requirements][source-3-3].

Registry prerequisites require a unique descriptive kebab-case ID without `zed`
or `extension`, English user-facing text, needed resources only, and manual
testing of the submitted commit. Language servers/debug adapters must be
discovered or downloaded rather than bundled. Theme and icon-theme packages have
separate category restrictions; scope language packages to the language and
related dialects. Agent-server/slash-command submissions are deprecated and no
longer accepted; use the ACP Registry for new agent-server distribution. MCP
extensions must contain only one server and have a documented future MCP
registry transition. Existing compatibility work and new publication eligibility
are separate decisions. [Category requirements][source-3-2].

Read [language and debugger assets](languages-and-debuggers.md) for queries, DAP
and declarative assets. Refresh differing API ranges, unpublished hooks, or
changed registry schemas.

[source-3-1]: https://zed.dev/docs/extensions/publishing/publishing-guide
[source-3-2]: https://zed.dev/docs/extensions/publishing/prerequisites
[source-3-3]: https://zed.dev/docs/extensions/publishing/license-requirements
