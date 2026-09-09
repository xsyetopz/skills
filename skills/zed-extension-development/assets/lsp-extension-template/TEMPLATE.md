# Zed Rust/WASM LSP starter

Replace placeholders. Select a Rust edition, `zed_extension_api`, and WASM
target supported by the target Zed version. The documented baseline uses
`wasm32-wasip2`.

The starter resolves a server with `Worktree::which`. Replace the executable and
arguments with the actual server interface. For managed downloads, pin
version/platform/architecture and handle storage, extraction, and failures.

Build for the compatible WASM target. Check server startup and shutdown through
a Dev Extension and its logs.
