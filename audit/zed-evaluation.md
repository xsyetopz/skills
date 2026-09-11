# Zed extension evaluation

Evaluated 2026-09-12. Kept Zed extension development explicit-only and
consolidated nine inherited reference files into two: host/API/registry and
language/debugger/assets. Rechecked official development, language and
publication documentation plus pinned host implementation.

## Concrete grammar assets

The language starter previously guessed `identifier` for a function name while
leaving its grammar unspecified. Replaced that mismatch with a coherent Bash
example using tree-sitter-bash v0.25.1, pinned to
`a06c2e4415e9bc0346c6b86d401879ffb44058f7`. Bash function names use `word`.
Configuration and queries now agree; identity/author/repository placeholders
remain explicit adaptation points. The guide warns against duplicating Zed's
existing Bash support merely to configure a server.

Tree-sitter 0.27.0 compiled the pinned parser and ran the actual queries against
nested functions, Unicode, comments and strings containing fake declarations.
Only the two real functions were outlined. Highlight captures included quoted
and raw strings, a comment and a variable name. Incomplete input still produced
string highlights. An `identifier` mutation failed query compilation. The CLI
warned that global parser directories were unconfigured but resolved the parser
from the checkout; no global configuration was changed. These checks validate
parser/query behavior, not Zed's visual rendering or an exhaustive Bash
highlighting scheme. Artifact: `/tmp/zed-bash-grammar-evidence`.

## Real WASM build and host loading

Instantiated the LSP starter with published `zed_extension_api = 0.7.0`, Rust
2024, `bash-language-server start` and the host's `Shell Script` language.
Installed rustup stable's `wasm32-wasip2` target. The first build failed because
Cargo found Homebrew's compiler without that target; setting `RUSTC` to the
rustup compiler resolved the actual installation mismatch. Locked release builds
then passed. Added this troubleshooting boundary to the template guide.

Downloaded official Zed 1.19.2 aarch64 into `/tmp/zed-host-evidence`, copied the
app from a read-only disk-image mount and detached the image. Version/help
verified `--user-data-dir`. An isolated profile with telemetry and updates
disabled loaded a fixture symlink under its installed-extension directory,
following the pinned host's discovery implementation.

A fixture-only diagnostic in `Extension::new` emitted
`SKILL_FIXTURE_EXTENSION_LOADED`; the generated extension index registered the
Rust extension and Shell Script server contribution. The repository starter has
no diagnostic marker. This demonstrates actual WASM host loading/instantiation,
not merely compilation. The process was forcibly stopped after the bounded
20-second test; no temporary host process remained. No ordinary installation or
profile was modified. Artifact: `/tmp/zed-wasm-evidence`; captured host output:
`/tmp/zed-host-evidence/run.log`.

No real LSP initialization/diagnostic exchange, visual outline assertion,
managed download, DAP session or GUI Dev Extension installation was exercised.
The source-backed installed-directory fixture does not prove those workflows.

## Host ownership and publication

Pinned `crates/project/src/lsp_store.rs` resolves explicit user binary paths
before adapter callbacks. It merges shell environment and user overrides, and
uses empty arguments for an explicitly configured path without arguments.
Removed redundant environment collection from the starter and documented this
order rather than adding duplicate settings policy. Replaced the error's
nonexistent managed-download option with actual PATH/configuration guidance.
Removed the duplicate Rust example from the reference; it now links the asset.

Refreshed registry category, license and publication rules. Deprecated agent
server submissions route to ACP Registry; MCP packages contain one server and
have a documented future registry transition. No registry submission or remote
write was performed. These are current documented requirements, not a promise
that a package will be accepted.

## Package verification

Official skills-ref and skill-creator validators, strict Markdown, local links,
TOML parsing and Rust formatting passed. The instantiated starter's real
wasm32-wasip2 build and host load provide distinct evidence from the native
Tree-sitter query tests. No generated grammar, target directory, disk image or
editor profile was added to the repository.
