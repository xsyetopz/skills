# Zed Rust/WASM LSP starter

Replace placeholders. Select a Rust edition, `zed_extension_api`, and WASM
target supported by the target Zed version. The documented baseline uses
`wasm32-wasip2`.

The starter resolves a server with `Worktree::which`. Replace the executable and
arguments with the actual server interface. For managed downloads, pin
version/platform/architecture and handle storage, extraction, and failures.

Build for the compatible WASM target. Verify that Cargo invokes the compiler
whose sysroot contains that target: mixed Homebrew/rustup PATH entries can run a
different `rustc` even after `rustup target add` succeeds. An explicit `RUSTC`
pointing to `rustup which --toolchain stable rustc` resolves that installation
mismatch without changing the project toolchain policy.

For a concrete user-installed Bash server fixture, substitute
`bash-language-server`, arguments `["start"]`, and language `Shell Script`. This
is a server adapter, not a grammar implementation; use the host's existing
language support rather than adding a duplicate grammar. Replace metadata with
the actual extension's identity before publishing.

Check server startup and shutdown through a Dev Extension and its logs.
