# Manifest, crate, and build

Cards for the files every extension needs and for building the Rust crate
into the `extension.wasm` that Zed loads. Host facts: Zed v1.21.0 (stable
on 2026-09-25) and its source at the `v1.21.0` tag. Crate facts:
`zed_extension_api` 0.7.0, the newest release on crates.io. "Executed"
marks a result from [`assets/examples/verify.sh`][verify] on macOS arm64
with rustup Rust 1.98.1.

## Contents

- [Extension manifest](#extension-manifest)
- [Ignored manifest keys](#ignored-manifest-keys)
- [Extension crate](#extension-crate)
- [API version and Zed compatibility](#api-version-and-zed-compatibility)
- [register\_extension and Extension::new](#register_extension-and-extensionnew)
- [Build for wasm32-wasip2](#build-for-wasm32-wasip2)
- [Toolchain that owns the target](#toolchain-that-owns-the-target)
- [Process execution capability](#process-execution-capability)
- [Dev extension install](#dev-extension-install)

## Extension manifest

**Definition.** `extension.toml` at the extension root, deserialized into
`ExtensionManifest`. `id`, `name`, `version`, and `schema_version` are
required. Zed treats `description`, `repository`, and `authors` as
optional; the registry packager requires them. Feature tables:
`grammars`, `language_servers`, `context_servers`, `debug_adapters`,
`debug_locators`, `capabilities`, and `snippets`. Zed adds
`languages/*/`, `themes/*.json`, and `icon_themes/*.json` on its own, and
sets `lib.kind = "Rust"` when a `Cargo.toml` exists ([manifest
source][manifest-rs], [`populate_defaults`][builder-rs]).

**Use when.**

- Every extension, including theme-only and snippet-only ones.
- Adding a feature: each grammar, language server, MCP server, debug
  adapter, and locator needs its own table.

**Do not use when.**

- A legacy `extension.json` exists. The registry packager fails with
  "The `extension.json` manifest format has been superseded by
  `extension.toml`" ([package-extensions.js][registry-package]).
- Listing `languages`, `themes`, or `icon_themes` paths by hand for files
  in the default folders. Zed discovers them; a hand list only
  duplicates the discovered entries and goes stale.

**Example.** Runnable: `assets/examples/makefile/extension.toml`.

```toml
id = "makefile"
name = "Makefile"
version = "0.1.0"
schema_version = 1
authors = ["Example Maintainer <maintainer@example.com>"]
description = "GNU Make syntax highlighting, outline, and recipe injection"
repository = "https://github.com/example/zed-makefile"
snippets = ["./snippets/makefile.json"]

[grammars.make]
repository = "https://github.com/tree-sitter-grammars/tree-sitter-make"
rev = "5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d"
```

**Cost removed.** Registry CI rejects a manifest whose `schema_version`
is not `1`, whose name starts or ends with "Zed" or contains "extension",
or whose description is not longer than the name
([validation.js][registry-validation], [`zed-extension` CLI][cli-rs]).
`check_extension.py --registry` reports each as an `ERROR` line, so the
count goes from N to 0 before the PR is opened.

**Verify.**

1. `python3 scripts/check_extension.py --registry EXT_DIR` prints
   `0 errors`. Executed on all six fixtures.
1. After the dev install, the Extensions page lists the extension under
   its `name`. Not runnable here: Zed is not installed.

## Ignored manifest keys

**Definition.** `ExtensionManifest` does not use serde's
`deny_unknown_fields` ([source][manifest-rs]), so a misspelled table
such as `[language-servers.x]` (hyphen) parses without error and is
dropped; its feature never registers. The multi-language example on the
Zed docs languages page shows `[language-servers.my-language-server]`,
but the struct field is `language_servers`. Inferred from the source,
not observed in a running Zed.

**Use when.**

- A server, grammar, or MCP server does nothing and the Zed log has no
  error about it.
- Copying a snippet from the docs or another extension.

**Do not use when.**

- The key is `[language_servers.<id>].name`. The docs show it and Zed
  ignores it harmlessly; the table key is the server ID.

**Example.** The failure, reproduced by the verify script's mutant:

```toml
[language-servers.x]
languages = ["Makefile"]
```

```text
ERROR extension.toml: unknown key `language-servers` is ignored by
Zed; did you mean `language_servers`?
```

**Cost removed.** One silent no-op registration per misspelled key,
turned into one `ERROR` line from the checker. Without the checker, the
only sign is a missing server in the running editor.

**Verify.**

1. `sh assets/examples/verify.sh` prints `ok   mutant rejected:
   hyphenated [language-servers] table`. Executed.
1. After fixing the key, `check_extension.py` prints `0 errors`.

## Extension crate

**Definition.** A Cargo package at the extension root with
`[lib] crate-type = ["cdylib"]` and a `zed_extension_api` dependency.
Zed runs `cargo build --target wasm32-wasip2 [--release]
--target-dir <ext>/target`, reads
`target/wasm32-wasip2/<profile>/<package name with - replaced by _>.wasm`,
strips most custom sections, and writes `extension.wasm`
([builder source][builder-rs]). Only language server, MCP server, and
debugger features need Rust ([developing extensions][dev-docs]).

**Use when.**

- The manifest declares `language_servers`, `context_servers`,
  `debug_adapters`, or `debug_locators`.

**Do not use when.**

- The extension only provides grammars, queries, themes, icon themes,
  or snippets. The registry prerequisites say "Do not include any Rust
  code should your extension not also provide language servers"
  ([prerequisites][prereq]).
- Renaming the dependency (`zed = { package = "zed_extension_api"
  }`). `register_extension!` expands to `zed_extension_api::` paths, so
  the build fails with ``error[E0433]:
  cannot find module or crate `zed_extension_api` `` (Executed in this
  session). Write
  `use zed_extension_api as zed;` instead.

**Example.** Runnable: `assets/examples/marksman-lsp/Cargo.toml`.

```toml
[package]
name = "marksman-lsp"
version = "0.1.0"
edition = "2021"
publish = false
license = "MIT"

[lib]
crate-type = ["cdylib"]

[dependencies]
zed_extension_api = "=0.7.0"
```

The `=` pin keeps `Cargo.lock` and CI on the reviewed API. A plain
`"0.7.0"` (caret) also stays on 0.7.x, because a 0.x caret does not
cross a minor version. Zed's own HTML extension uses `"0.7.0"`
([html Cargo.toml][html-cargo]).

**Cost removed.** A failed Zed load. Without `cdylib` there is no
`.wasm` for Zed to read; the checker reports `[lib]
crate-type must include "cdylib"`.

**Verify.**

1. `cargo build --release --target wasm32-wasip2` writes
   `target/wasm32-wasip2/release/marksman_lsp.wasm`. Executed:
   355,398 B (machine-specific, Rust 1.98.1).
1. `check_extension.py EXT_DIR` prints `0 errors`.

## API version and Zed compatibility

**Definition.** `zed_extension_api` embeds its version in a 6-byte custom
section named `zed:api-version` (three big-endian `u16`s). Zed accepts
only versions in `wasm_api_version_range`: 0.0.1 to 0.7.0 on the stable
and preview channels of v1.21.0, up to 0.8.0 on dev and nightly
([wit.rs][wit-rs]). The crate is 0.8.0 in the repository but has
`publish = false`, so crates.io tops out at 0.7.0 ([crate
Cargo.toml][api-cargo], [crates.io][crate]).

**Use when.**

- Choosing the dependency version: take the newest crates.io release
  that the oldest supported Zed still accepts.
- A user reports that the extension installs on nightly but not on
  stable.

**Do not use when.**

- Reading the compatibility table in the crate README. On `main` it
  stops at `0.192.x → 0.6.0` and omits 0.7.0; `wit.rs` is the authority.
- Copying `zed_extension_api = "0.1.0"` from the `developing-extensions`
  page. It is an illustration; the page itself says to use the latest
  version.

**Example.** Read the section from a build:

```sh
python3 scripts/wasm_api_version.py \
  target/wasm32-wasip2/release/marksman_lsp.wasm --max 0.7.0
```

```text
zed:api-version 0.7.0
```

**Cost removed.** Shipping a build that stable Zed rejects. With
`--max 0.7.0` the script exits 1 with `0.8.0 is newer than 0.7.0` before
publishing (unit test executed).

**Verify.**

1. `verify.sh` prints `zed:api-version 0.7.0` for all three crates.
   Executed.
1. `python3 scripts/test_wasm_api_version.py` covers core modules,
   nested components, the missing section, and `--max`. Executed: 6
   tests OK.

## register\_extension and Extension::new

**Definition.** `zed::register_extension!(T)` exports the component
function `init-extension`, which sets the WASI working directory from
`PWD`, forbids `chdir`, and stores `Box::new(T::new())` in a global that
every later call uses ([extension_api.rs 0.7.0][api-src]). `new` takes
no arguments and cannot fail. The one instance lives until Zed unloads
or reloads the extension.

**Use when.**

- Exactly once per crate, on the type that implements `zed::Extension`.
- Keeping cross-call state, such as a cached binary path, in the struct.

**Do not use when.**

- Doing I/O or downloads in `new`: there is no `Result` to report
  errors, and the worktree is not known yet. Do that work in the first
  `language_server_command` call.
- Leaving the macro out. The trait still compiles, but the link fails:
  `failed to decode world from module ... failed to find export of
  function 'init-extension'` (Executed in this session).

**Example.** Runnable: `assets/examples/marksman-lsp/src/lib.rs`.

```rust
use zed_extension_api::{self as zed, LanguageServerId, Result};

struct MarksmanExtension {
    cached_binary_path: Option<String>,
}

impl zed::Extension for MarksmanExtension {
    fn new() -> Self {
        Self {
            cached_binary_path: None,
        }
    }
    // language_server_command and other hooks
}

zed::register_extension!(MarksmanExtension);
```

**Cost removed.** A module that Zed cannot instantiate becomes a
`cargo build` failure.

**Verify.**

1. `cargo build --release --target wasm32-wasip2` succeeds. Executed.
1. Remove the macro: the build fails with the `init-extension` message
   above. Executed on a scratch copy.

## Build for wasm32-wasip2

**Definition.** `wasm32-wasip2` is the Rust target Zed builds extensions
for (`RUST_TARGET` in [the builder][builder-rs]); the output is a
WebAssembly component. `cfg!` describes the WASI target, not the user's
OS, and `std::env::var` does not see the user's environment. Use
`zed::current_platform()` and `Worktree::shell_env()` instead
([developing extensions][dev-docs]).

**Use when.**

- Checking a Rust change before a dev install.
- CI for an extension repository.

**Do not use when.**

- Taking `cargo check` or `cargo test` on the host target as proof that
  the extension builds. They skip the component link step, so a missing
  `init-extension` export passes. Use them for pure logic only.
- Branching on `cfg!(target_os = "macos")` to choose a download. Match
  on `zed::current_platform()`.

**Example.**

```sh
rustup target add wasm32-wasip2
cargo build --release --target wasm32-wasip2
cargo test                      # pure helpers, host target
cargo clippy --target wasm32-wasip2 -- -D warnings
```

Executed output from `verify.sh` (sizes are machine-specific):

```text
ok   marksman-lsp: wasm32-wasip2 build, zed:api-version 0.7.0, 355398 B
ok   marksman-lsp: test result: ok. 4 passed; 0 failed; ...
ok   marksman-lsp: cargo clippy -D warnings (wasm32-wasip2)
```

**Cost removed.** The rebuild-and-reinstall loop in Zed for compile
errors, where Zed reports only "failed to build extension" plus cargo
stderr. A dev install runs the same `cargo build` in debug mode
(`CompileExtensionOptions::dev()` sets `release: false`); the registry
packager builds with `--release`.

**Verify.**

1. The command exits 0 and the `.wasm` file exists.
1. `wasm_api_version.py` prints the expected version.

## Toolchain that owns the target

**Definition.** Zed runs `rustc --print target-libdir --target
wasm32-wasip2` with the `rustc` on `PATH` and, if that directory is
missing, runs `rustup target add wasm32-wasip2`
([builder source][builder-rs]). When a Homebrew `rustc` precedes
rustup's on `PATH`, rustup installs the target into its own toolchain
and the Homebrew compiler still lacks it.

**Use when.**

- The build fails with ``error[E0463]: can't find crate for `core` ``
  although `rustup target list --installed` lists `wasm32-wasip2`.

**Do not use when.**

- Nix or fenix toolchains. Add `wasm32-wasip2` to the toolchain's
  `targets` as the docs describe; `rustup` does not own it.

**Example.** Reproduced with Homebrew Rust 1.98.1 in `/opt/homebrew/bin`
next to the rustup stable toolchain.

```sh
rustc --print target-libdir --target wasm32-wasip2  # Homebrew: missing
PATH="$(dirname "$(rustup which rustc)"):$PATH" \
  cargo build --release --target wasm32-wasip2
```

```text
error[E0463]: can't find crate for `core`      # with Homebrew cargo
Finished `release` profile [optimized] target(s)   # with rustup PATH
```

`verify.sh` makes this switch itself and prints the `rustc` it used.
That Zed's own dev install fails the same way when launched from such a
shell is inferred from the builder source, not executed.

**Cost removed.** A build failure that `rustup target add` cannot fix.
The E0463 error disappears after the `PATH` change.

**Verify.**

1. `ls "$(rustc --print target-libdir --target wasm32-wasip2)"` lists
   `libcore-*.rlib`.
1. The build finishes. Executed.

## Process execution capability

**Definition.** `zed_extension_api::process::Command::output()` runs a
host process only when two grants allow it: a `[[capabilities]]` entry
with `kind = "process:exec"` in `extension.toml`, and the user's
`granted_extension_capabilities` setting ([capability
granter][granter-rs], [capabilities docs][caps-docs]). In `args`, `*`
matches one argument and a final `**` matches all remaining ones. The
process inherits Zed's environment plus the `env` you pass.

**Use when.**

- The extension needs an answer only a host tool gives, such as
  `xcrun -f lldb-dap` for Xcode's adapter path.

**Do not use when.**

- Finding a binary on `PATH`. `Worktree::which` needs no capability.
- Launching a language server, MCP server, or debug adapter. Return a
  `Command` or `DebugAdapterBinary` and let Zed start it.
- Broad grants such as `command = "*"`. Users can restrict grants, and
  the prerequisites forbid working around API limits.

**Example.** Runnable: `assets/examples/lldb-dap-debugger/`.

```toml
[[capabilities]]
kind = "process:exec"
command = "xcrun"
args = ["-f", "lldb-dap"]
```

```rust
let output = Command::new("xcrun")
    .args(["-f", ADAPTER])
    .envs(worktree.shell_env())
    .output()?;
```

Without the manifest entry the call returns "capability for
process:exec xcrun [\"-f\", \"lldb-dap\"] was not listed in the
extension manifest" ([manifest source][manifest-rs]).

**Cost removed.** A runtime error on every invocation.
`check_extension.py` checks that each capability has `command` and
`args`; only Zed checks the grant match.

**Verify.**

1. `check_extension.py` prints `0 errors`. Executed.
1. In Zed, the adapter path resolves on a Mac without `lldb-dap` on
   `PATH` (Not runnable here). `xcrun -f lldb-dap` printed a toolchain
   path. Executed.

## Dev extension install

**Definition.** The `zed: install dev extension` action ("Install Dev
Extension" on the Extensions page) asks for a directory, builds it as
above, and loads it. A published copy is uninstalled first and shows as
"Overridden by dev extension". Logs go to `Zed.log` (`zed: open log`);
`zed --foreground` also shows INFO-level logs and the extension's
`println!`/`dbg!` output ([developing extensions][dev-docs]).
`zed --user-data-dir DIR` gives extensions, logs, and the database a
separate directory, so the dev install leaves the published copy in the
normal profile alone ([CLI args][zed-cli]). Grammars need wasi-sdk: Zed
downloads it, or uses `WASI_SDK_PATH` when that directory contains
`bin/clang`.

**Use when.**

- After `verify.sh`-style checks pass, to test what only the host shows:
  server start, highlighting with a real theme, outline, and
  installation status messages.

**Do not use when.**

- As the first build check. Zed shows only "failed to build extension"
  plus stderr; run `cargo build` and the checkers first.
- As proof that the registry build works. The registry's `zed-extension`
  packager also compiles every query against the grammar and rejects
  unsupported files ([CLI source][cli-rs]).

**Example.** Not runnable here: Zed is not installed.

```sh
zed --foreground --user-data-dir /tmp/zed-dev   # isolated profile
# In Zed: cmd-shift-p, "zed: install dev extension",
# select assets/examples/makefile, then open samples/Makefile.
# Check: language picker shows "Makefile", outline lists `all`,
# `build/app`, `clean`, recipe lines highlight as Shell Script.
```

**Cost removed.** Publishing just to find host-only failures. Target: 0
ERROR-level `Zed.log` lines that name the extension ID.

**Verify.**

1. The Extensions page shows the dev extension as installed.
1. The expected language, server, theme, or icon theme appears in its
   picker, and `Zed.log` has no error for the extension ID.

[verify]: ../assets/examples/verify.sh
[dev-docs]: https://zed.dev/docs/extensions/developing-extensions
[zed-cli]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/cli/src/main.rs
[caps-docs]: https://zed.dev/docs/extensions/capabilities
[prereq]: https://zed.dev/docs/extensions/publishing/prerequisites
[crate]: https://crates.io/crates/zed_extension_api
[api-src]: https://docs.rs/crate/zed_extension_api/0.7.0/source/src/extension_api.rs
[manifest-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_manifest.rs
[builder-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_builder.rs
[cli-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_cli/src/main.rs
[wit-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_host/src/wasm_host/wit.rs
[granter-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_host/src/capability_granter.rs
[api-cargo]: https://github.com/zed-industries/zed/blob/main/crates/extension_api/Cargo.toml
[html-cargo]: https://github.com/zed-industries/zed/blob/v1.21.0/extensions/html/Cargo.toml
[registry-validation]: https://github.com/zed-industries/extensions/blob/main/src/lib/validation.js
[registry-package]: https://github.com/zed-industries/extensions/blob/main/src/package-extensions.js
