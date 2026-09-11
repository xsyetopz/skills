# VS Code Bun/TypeScript starter

This starter uses Bun for build/test tooling and Biome for checks. Bun APIs are
unavailable in the VS Code extension host.

Replace placeholders. Select compatible Bun, Biome, TypeScript, VS Code and Node
declarations, and vsce versions. Match the engine and Node types to the oldest
supported host. Set the real repository URL, include the selected license file,
and generate the package-manager lockfile.

Include the browser entrypoint only for web support. Set trust and
virtual-workspace declarations from implemented behavior. Replace the example
command with the feature. The supplied command encodes nonempty selections as
JSON string literals in one edit/undo transaction; it does not execute workspace
code or use local filesystem paths.

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

For retained web support, run equivalent assertions with `@vscode/test-web` and
a browser-compatible test bundle. Keep its test module under the extension
development directory: the runner serves it relative to that directory. Use the
runner's `--coi` option when cross-origin isolation is required by the selected
host. Confirm that assertions actually execute, including a negative control; an
exit code alone can miss a host that closes before tests start. Do not disable
browser security to make tests pass.
