# Language servers

Cards for starting a language server from an extension. The runnable
crate [`assets/examples/marksman-lsp/`][crate-dir] attaches Marksman to
Zed's built-in `Markdown` language and resolves the binary from `PATH`,
then a cached download, then a pinned or the latest GitHub release. Host
behavior: Zed v1.21.0 source. API signatures: `zed_extension_api` 0.7.0.
Pure helpers ran as native `cargo test` (Executed, 4 tests). The
Zed-side flow is Not runnable here: Zed is not installed.

## Contents

- [Language server registration](#language-server-registration)
- [language\_server\_command](#language_server_command)
- [Worktree::which](#worktreewhich)
- [Worktree::shell\_env](#worktreeshell_env)
- [Latest release and platform asset](#latest-release-and-platform-asset)
- [Pinned GitHub release](#pinned-github-release)
- [download\_file and archive types](#download_file-and-archive-types)
- [make\_file\_executable](#make_file_executable)
- [Version-scoped download cache](#version-scoped-download-cache)
- [Installation status](#installation-status)
- [User binary settings take precedence](#user-binary-settings-take-precedence)
- [Server options and configuration](#server-options-and-configuration)
- [npm-distributed servers](#npm-distributed-servers)

## Language server registration

**Definition.** A `[language_servers.<id>]` table in `extension.toml`.
`<id>` is the server name Zed passes to every hook as `LanguageServerId`
and users write in `lsp.<id>` settings. `languages` (or the older single
`language`) lists Zed language names, each of which must match a
`config.toml` `name` exactly. `language_ids` maps a Zed language name to the LSP
`languageId` ([languages docs][lang-docs], [manifest source][manifest-rs]).

**Use when.**

- The extension starts an LSP server for its own language or a built-in
  one (the built-in Markdown language is named `Markdown` in
  [its config.toml][md-config]).

**Do not use when.**

- The language name differs at all, for example `markdown`, or `Shell`
  for `Shell Script`. The server never attaches and Zed shows no error.
- Writing `[language-servers.<id>]` with a hyphen, as the docs'
  multi-language example does. See
  [Ignored manifest keys](manifest-and-build.md#ignored-manifest-keys).

**Example.** Runnable: `assets/examples/marksman-lsp/extension.toml`.

```toml
[language_servers.marksman]
name = "Marksman"
languages = ["Markdown"]
```

One server for several languages:

```toml
[language_servers.web-lsp]
languages = ["HTML", "CSS"]

[language_servers.web-lsp.language_ids]
"HTML" = "html"
"CSS" = "css"
```

**Cost removed.** A server that never attaches. `check_extension.py`
warns when a listed language is not defined in the extension
(`'Markdown' is not defined here; it must equal the name of a
built-in or installed language exactly`); compare each warning against
the built-in names.

**Verify.**

1. `check_extension.py` prints 0 errors. Executed. The one warning, for
   `Markdown`, is expected because Markdown is built in.
1. In Zed, open a `.md` file and run `dev: open language server logs`;
   `marksman` is listed (Not runnable here).

## language\_server\_command

**Definition.** `fn language_server_command(&mut self, id:
&LanguageServerId, worktree: &Worktree) -> Result<Command>` returns
`Command { command, args, env }`. Zed resolves a relative `command`
against the extension's work directory (`work_dir().join(path)` in
[extension.rs][extension-rs]). The default implementation returns
``Err("`language_server_command` not implemented")``
([trait docs][trait-docs]).

**Use when.**

- Every `[language_servers.<id>]` entry. Match on `id.as_ref()` when one
  crate serves several servers.

**Do not use when.**

- Spawning the server yourself with `process::Command`. Zed owns the
  server process, its stdio, and its restarts.
- Adding the user's shell environment to `env`. Zed already merges
  `shell_env()` under the returned `env` ([lsp_store.rs][lsp-store]).

**Example.** Runnable: `assets/examples/marksman-lsp/src/lib.rs`.

```rust
fn language_server_command(
    &mut self,
    id: &LanguageServerId,
    worktree: &zed::Worktree,
) -> Result<zed::Command> {
    Ok(zed::Command {
        command: self.binary(id, worktree)?,
        args: vec!["server".to_string()],
        env: Default::default(),
    })
}
```

`server` is the Marksman subcommand that speaks LSP on stdin and stdout
([Program.fs][marksman-cli]).

**Cost removed.** Scattered binary resolution: one code path, and Zed
shows each returned error string for that server.

**Verify.**

1. `cargo build --release --target wasm32-wasip2` succeeds. Executed.
1. In Zed, the server log shows the resolved path and the `server`
   argument (Not runnable here).

## Worktree::which

**Definition.** `Worktree::which(&self, binary_name: &str) ->
Option<String>` returns a binary's path if it is on the worktree's
`$PATH` ([extension.wit][wit-extension]).

**Use when.**

- Before any download, so a user-installed or project-pinned server
  wins. The registry prerequisites say to download the server or find
  it in the user's environment, never to bundle it
  ([prerequisites][prereq]).

**Do not use when.**

- The user set `lsp.<id>.binary.path`: Zed then never calls the
  extension (see
  [User binary settings](#user-binary-settings-take-precedence)).
- Reading `std::env::var("PATH")`. In WASI it does not reflect the
  user's shell.

**Example.**

```rust
if let Some(path) = wt.which("marksman") {
    return Ok(path);
}
```

**Cost removed.** A download and a second copy of an installed server.
The server log shows the `PATH` location instead of the extension
directory.

**Verify.**

1. Code review: `which` runs before `cached_binary_path` and `download`
   in `binary()`.
1. In Zed with `marksman` on `PATH`, no `marksman-*` directory appears in
   the extension work directory (Not runnable here).

## Worktree::shell\_env

**Definition.** `Worktree::shell_env(&self) -> EnvVars` returns the
user's shell environment in the worktree as `Vec<(String,
String)>` ([extension.wit][wit-extension]). It is the only way to read
user environment variables: `std::env::var` in the WASI guest does not
see them ([developing extensions][dev-docs]).

**Use when.**

- Reading a user setting that lives in the shell, such as
  `MARKSMAN_RELEASE`, which the example uses to pin a release.
- Passing the user's `PATH` and `DEVELOPER_DIR` to
  `process::Command::envs`; otherwise that process inherits only Zed's
  environment ([host run_command][host-rs]).

**Do not use when.**

- Filling `Command.env` for the language server. Zed already merges the
  shell environment; copying it in hides which variables the extension
  sets.

**Example.**

```rust
const PIN_VAR: &str = "MARKSMAN_RELEASE";

fn release_pin(env: &[(String, String)]) -> Option<&str> {
    env.iter()
        .find(|(key, value)| key == PIN_VAR && !value.is_empty())
        .map(|(_, value)| value.as_str())
}

let env = wt.shell_env();
let path = download(id, release_pin(&env))?;
```

**Cost removed.** Guessing what environment the guest sees. The unit
test `pin_comes_from_a_non_empty_shell_variable` fixes the behavior for
set, empty, and missing values.

**Verify.**

1. `cargo test` passes `pin_comes_from_a_non_empty_shell_variable`.
   Executed.
1. In Zed with `MARKSMAN_RELEASE=2026-02-08` exported in the shell,
   `marksman-2026-02-08/` is created (Not runnable here).

## Latest release and platform asset

**Definition.** `latest_github_release(repo, GithubReleaseOptions {
require_assets, pre_release })` returns `GithubRelease { version,
assets: [GithubReleaseAsset { name, download_url }] }`, with `repo` as
`"owner/name"`. `current_platform()` returns `(Os, Architecture)`: `Os`
is Mac, Linux, or Windows; `Architecture` is Aarch64, X86, or X8664
([github.wit][wit-github], [platform.wit][wit-platform]).

**Use when.**

- The server publishes prebuilt binaries as GitHub release assets with
  stable per-platform names.

**Do not use when.**

- The server ships on npm (see
  [npm-distributed servers](#npm-distributed-servers)).
- Guessing asset names. Read the real release. Marksman's 2026-02-08
  assets are `marksman-macos` (a universal x86_64 and arm64 Mach-O,
  checked with `file` in this session), `marksman-linux-x64`,
  `marksman-linux-arm64`, the musl variants, and `marksman.exe`
  ([releases][marksman-releases]).
- A catch-all arm that returns some asset for every platform. Return
  `None` and a clear error for unsupported platforms.

**Example.**

```rust
fn asset_name(os: zed::Os, arch: zed::Architecture) -> Option<&'static str> {
    use zed::{Architecture as A, Os};
    match (os, arch) {
        (Os::Mac, A::Aarch64 | A::X8664) => Some("marksman-macos"),
        (Os::Linux, A::X8664) => Some("marksman-linux-x64"),
        (Os::Linux, A::Aarch64) => Some("marksman-linux-arm64"),
        (Os::Windows, A::X8664) => Some("marksman.exe"),
        _ => None,
    }
}
```

**Cost removed.** A wrong-architecture binary that fails with "exec
format error" at server start. The test `maps_every_published_platform`
covers every published asset and two unsupported pairs.

**Verify.**

1. `cargo test` passes `maps_every_published_platform`. Executed.
1. Compare the match arms with `gh release view -R
   artempyanykh/marksman --json assets --jq '.assets[].name'`. Executed
   on 2026-09-25.

## Pinned GitHub release

**Definition.** `github_release_by_tag_name(repo, tag)` returns the
release with exactly that tag, or an error if the tag does not exist
([github.wit][wit-github]).

**Use when.**

- The user or project needs a known server version, for example because
  a newer release changed protocol behavior.
- Reproducing a bug report against one server version.

**Do not use when.**

- As the only path. Without a pin, fall back to `latest_github_release`
  so new users get a working server.

**Example.**

```rust
fn fetch_release(pin: Option<&str>) -> Result<zed::GithubRelease> {
    match pin {
        Some(tag) => zed::github_release_by_tag_name(REPO, tag),
        None => zed::latest_github_release(
            REPO,
            zed::GithubReleaseOptions {
                require_assets: true,
                pre_release: false,
            },
        ),
    }
}
```

**Cost removed.** Version drift between machines: the same pin gives
the same asset name from the same tag.

**Verify.**

1. `cargo clippy --target wasm32-wasip2 -- -D warnings` is clean.
   Executed.
1. `gh release view 2026-02-08 -R artempyanykh/marksman --json assets`
   lists `marksman-macos`, `marksman-linux-x64`, `marksman-linux-arm64`,
   and `marksman.exe`. Executed.

## download\_file and archive types

**Definition.** `download_file(url, file_path, file_type)` fetches `url`
into `file_path` under the extension's work directory and rejects a path
that escapes it. `DownloadedFileType`:

- `Uncompressed` writes the body as-is.
- `Gzip` gunzips the body into one file.
- `GzipTar` extracts a `.tar.gz` into the directory.
- `Zip` extracts into the directory.

The call needs a user grant matching `download_file`; the default grant
allows any host ([host implementation][host-rs],
[default settings][default-settings]).

**Use when.**

- `Uncompressed`: single-file binaries such as `marksman-linux-x64`.
- `Gzip`: single-file `*.gz` assets.
- `GzipTar` or `Zip`: archives. Point `file_path` at a version
  directory and build the binary path inside it, as Zed's test extension
  does with `gleam-{version}/gleam` ([test extension][test-ext]).

**Do not use when.**

- Picking `Uncompressed` for an archive asset. The "binary" is then a
  tarball and the server fails to start.
- Downloading `Uncompressed` into a parent directory that does not exist
  yet. Create it with `std::fs::create_dir_all`; the prerequisites allow
  standard library file operations inside the work directory.

**Example.**

```rust
fs::create_dir_all(&dir).map_err(|e| format!("create {dir}: {e}"))?;
zed::download_file(
    &asset.download_url,
    &path,
    zed::DownloadedFileType::Uncompressed,
)?;
```

**Cost removed.** A second download of the same version. The download
runs only when `!is_file(&path)`, so each version costs one GitHub API
call and one asset download.

**Verify.**

1. Code review: `download_file` runs only inside `if !is_file(&path)`.
1. In Zed, the second server start downloads nothing: the log has no
   "Downloading" status (Not runnable here).

## make\_file\_executable

**Definition.** `make_file_executable(path)` sets the executable bits on
a file inside the work directory ([host implementation][host-rs]).
Downloads do not preserve modes.

**Use when.**

- After every `Uncompressed` or `Gzip` download of a program, and for
  archive entries when the archive may not keep the mode.

**Do not use when.**

- The binary came from `which`, user settings, or `node_binary_path()`.
  Those files are outside the work directory and not yours to change.

**Example.**

```rust
zed::make_file_executable(&path)?;
```

**Cost removed.** A "permission denied" failure at server start on macOS
and Linux.

**Verify.**

1. Code review: the call directly follows `download_file`.
1. In Zed, `ls -l` on the downloaded file shows `x` bits (Not runnable
   here).

## Version-scoped download cache

**Definition.** Store each release in `marksman-{version}/`. Keep the
resolved path in the extension struct (`cached_binary_path`), check it
with `fs::metadata` before any network call, and delete other
`marksman-*` directories after a successful download. Zed's test and
HTML extensions use this pattern ([test extension][test-ext],
[html.rs][html-rs]).

**Use when.**

- Any downloaded server. `language_server_command` runs on every server
  start, so without the cache every start hits the network.

**Do not use when.**

- The server came from `which`. Do not cache it, so a user upgrade on
  `PATH` takes effect.
- Deleting directories outside your prefix. Everything else the
  extension stores shares the work directory.

**Example.**

```rust
fn binary_path(version: &str, os: zed::Os) -> String {
    let file = match os {
        zed::Os::Windows => "marksman.exe",
        zed::Os::Mac | zed::Os::Linux => "marksman",
    };
    format!("{PREFIX}{version}/{file}")
}

fn stale_dirs<'a>(names: &'a [String], keep: &str) -> Vec<&'a str> {
    names
        .iter()
        .map(String::as_str)
        .filter(|name| name.starts_with(PREFIX) && *name != keep)
        .collect()
}
```

**Cost removed.** After the first start, both the GitHub API call and
the download. The cleanup keeps exactly one version directory on disk.

**Verify.**

1. `cargo test` passes `binary_lives_in_a_versioned_directory` and
   `keeps_only_the_current_version_directory`. Executed.
1. In Zed, after an upgrade only one `marksman-*` directory remains
   (Not runnable here).

## Installation status

**Definition.** `set_language_server_installation_status(id, status)`
shows progress in Zed's UI. Statuses: `None`, `CheckingForUpdate`,
`Downloading`, and `Failed(String)` ([extension.wit][wit-extension]).

**Use when.**

- Around each network step: `CheckingForUpdate` before the release
  lookup, `Downloading` before `download_file`, `None` after success.
- `Failed(message)` when resolution fails, so the message appears next
  to the server.

**Do not use when.**

- The binary came from `which` or the cache; nothing is being installed.

**Example.**

```rust
let path = download(id, release_pin(&env)).inspect_err(|error| {
    let failed =
        zed::LanguageServerInstallationStatus::Failed(error.clone());
    zed::set_language_server_installation_status(id, &failed);
})?;
```

**Cost removed.** An unexplained "server not running" state. Common
failures, such as no asset for the platform, show their reason without
a trip to `Zed.log`.

**Verify.**

1. Code review: every return path of `download` leaves the status at
   `None`, or at `Failed` through `binary()`.
1. In Zed with networking disabled, the server shows the `Failed`
   message (Not runnable here).

## User binary settings take precedence

**Definition.** In `get_language_server_binary`, when
`lsp.<id>.binary.path` is set, Zed launches that path directly and never
calls the extension, with `binary.arguments` (empty if unset) and
`shell_env()` plus `binary.env`. Otherwise Zed calls the extension,
merges `shell_env()` under the returned `env`, replaces the arguments
with `binary.arguments` when set, and adds `binary.env`
([lsp_store.rs][lsp-store]). The extension adapter binds
`LanguageServerBinaryOptions` to `_`, so `binary.ignore_system_version`
has no effect on extensions (inferred from
[the adapter source][adapter-rs]).

**Use when.**

- Documenting how users override the server.
- Deciding which checks the extension still needs: it does not read
  `binary.path` itself.

**Do not use when.**

- The server needs mandatory arguments (Marksman's `server`) and the
  user sets only `binary.path`. The arguments become empty, so tell
  users to set `arguments` too.

**Example.** User settings (`settings.json`):

```json
{
  "lsp": {
    "marksman": {
      "binary": {
        "path": "/opt/marksman/bin/marksman",
        "arguments": ["server"]
      }
    }
  }
}
```

**Cost removed.** Duplicate override logic in the extension. Zero lines
in the crate read `binary.path`, and the host behavior is the same for
every extension.

**Verify.**

1. `rg -n 'binary' assets/examples/marksman-lsp/src/lib.rs` finds only
   `binary_path` and `binary()`, no settings read.
1. In Zed with the setting above, the server log shows the configured
   path (Not runnable here).

## Server options and configuration

**Definition.** `language_server_initialization_options` returns the
JSON sent as `initializationOptions` in LSP `initialize`;
`language_server_workspace_configuration` returns the JSON Zed answers
`workspace/configuration` with. Both return
`Result<Option<serde_json::Value>>`, and the crate serializes the value
once. `LspSettings::for_worktree(name, worktree)` reads the user's
`lsp.<name>` object: `binary`, `initialization_options`, and `settings`
([settings.rs][settings-rs], [field types][settings-types]).

**Use when.**

- The server reads options at `initialize` or through
  `workspace/configuration`. Pass the user's values through, as Zed's
  HTML extension does for `settings` ([html.rs][html-rs]).
- Providing a default when the user sets nothing: return
  `Some(json!({...}))`.

**Do not use when.**

- Returning a JSON string inside the `Value`
  (`Value::String(to_string(..))`). The server receives a string instead
  of an object.
- Overwriting user values with defaults. Merge them; user values take
  precedence.

**Example.**

```rust
fn language_server_workspace_configuration(
    &mut self,
    id: &LanguageServerId,
    worktree: &zed::Worktree,
) -> Result<Option<zed::serde_json::Value>> {
    let settings = LspSettings::for_worktree(id.as_ref(), worktree)?;
    Ok(settings.settings)
}
```

**Cost removed.** A hard-coded configuration surface. Users configure
the server in `settings.json` without a new extension release.

**Verify.**

1. `cargo clippy -D warnings` is clean. Executed.
1. In Zed, `dev: open language server logs` with RPC tracing shows the
   user's `lsp.marksman.settings` in the `workspace/configuration`
   response (Not runnable here).

## npm-distributed servers

**Definition.** `npm_package_latest_version(name)`,
`npm_package_installed_version(name)`, and
`npm_install_package(name, version)` manage `node_modules/` in the
extension's work directory; the install needs the user's `npm:install`
grant. `node_binary_path()` returns Zed's managed Node.js
([nodejs.wit][wit-nodejs], [host][host-rs]).

**Use when.**

- The server is on npm and has no standalone binaries, such as
  `vscode-html-language-server` in Zed's HTML extension and
  `@modelcontextprotocol/server-memory` in the MCP example.

**Do not use when.**

- `which()` finds an install. Prefer it, as Zed's HTML extension does.
- Launching the package's `bin` shim with the system `node`. Run
  `node_binary_path()` with the entry script's absolute path.

**Example.** Runnable: `assets/examples/mcp-server-memory/src/lib.rs`.

```rust
let latest = zed::npm_package_latest_version(PACKAGE)?;
let installed = zed::npm_package_installed_version(PACKAGE)?;
if installed.as_deref() != Some(latest.as_str()) {
    zed::npm_install_package(PACKAGE, &latest)?;
}
let entry = env::current_dir()
    .map_err(|error| error.to_string())?
    .join(ENTRY); // node_modules/<pkg>/dist/index.js
Ok(zed::Command {
    command: zed::node_binary_path()?,
    args: vec![entry.to_string_lossy().into_owned()],
    env: Vec::new(),
})
```

`ENTRY` comes from the package's `bin` field:
`{"mcp-server-memory": "dist/index.js"}` in version 2026.8.31 (read from
registry.npmjs.org in this session).

**Cost removed.** A reinstall on every start: the version comparison
skips `npm_install_package` when the installed version matches.

**Verify.**

1. `cargo build --release --target wasm32-wasip2` of the MCP crate
   succeeds. Executed.
1. The registry document names the entry path. Executed:

   ```sh
   pkg=@modelcontextprotocol%2fserver-memory
   curl -s "https://registry.npmjs.org/$pkg/latest" | jq .bin
   ```

[crate-dir]: ../assets/examples/marksman-lsp/
[lang-docs]: https://zed.dev/docs/extensions/languages#language-servers
[dev-docs]: https://zed.dev/docs/extensions/developing-extensions
[prereq]: https://zed.dev/docs/extensions/publishing/prerequisites
[trait-docs]: https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/trait.Extension.html
[settings-rs]: https://docs.rs/crate/zed_extension_api/0.7.0/source/src/settings.rs
[settings-types]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.2.0/settings.rs
[wit-extension]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.6.0/extension.wit
[wit-github]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.6.0/github.wit
[wit-platform]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.6.0/platform.wit
[wit-nodejs]: https://docs.rs/crate/zed_extension_api/0.7.0/source/wit/since_v0.6.0/nodejs.wit
[manifest-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_manifest.rs
[extension-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension.rs
[lsp-store]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/project/src/lsp_store.rs
[adapter-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/language_extension/src/extension_lsp_adapter.rs
[host-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_host/src/wasm_host/wit/since_v0_8_0.rs
[default-settings]: https://github.com/zed-industries/zed/blob/v1.21.0/assets/settings/default.json
[md-config]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/grammars/src/markdown/config.toml
[html-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/extensions/html/src/html.rs
[test-ext]: https://github.com/zed-industries/zed/blob/v1.21.0/extensions/test-extension/src/test_extension.rs
[marksman-releases]: https://github.com/artempyanykh/marksman/releases
[marksman-cli]: https://github.com/artempyanykh/marksman/blob/main/Marksman/Program.fs
