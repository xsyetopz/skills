# VS Code Bun/TypeScript starter

This starter uses Bun for build/test tooling and Biome for checks. Bun APIs are
unavailable in the VS Code extension host.

Replace placeholders. Select compatible Bun, Biome, TypeScript, VS Code and Node
declarations, and vsce versions. Match the engine and Node types to the oldest
supported host. Set the real repository URL, include the selected license file,
and generate the package-manager lockfile.

The starter targets the desktop extension host. Add a browser entrypoint and web
test tooling only when web support is required. Set trust and virtual-workspace
declarations from implemented behavior. Replace the example command with the
feature. The supplied command encodes nonempty selections as JSON string
literals in one edit/undo transaction; it does not execute workspace code or use
local filesystem paths.

Select `__VSCODE_TEST_ELECTRON_VERSION__` and a concrete
`__VSCODE_TEST_VERSION__` matching the supported host. `bun run test` builds
production entrypoints and runs behavioral assertions in a real desktop host. It
downloads the selected host unless `VSCODE_EXECUTABLE_PATH` supplies an existing
executable; `VSCODE_TEST_VERSION` can select another test version. Temporary
user data and extension directories are cleaned after the run. A desktop session
(or supported virtual display on Linux) is required.

Run `bun run check` for non-mutating source checks and the desktop host test.
Use `bun run format` to apply formatting. Check affected extension-host
behavior. For VSIX changes, build production output and inspect the package file
list.

For added web support, follow the host reference and run equivalent assertions
with `@vscode/test-web`. Confirm that assertions execute, including a negative
control; an exit code alone can miss a host that closes before tests start.
