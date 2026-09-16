# Desktop VS Code extension: one edit transaction

This is a native Node/TypeScript template, not a requirement to migrate the
project's package manager or formatter. Integrate the source and host tests into
existing tooling when a project already exists. The fixture has no runtime npm
dependencies: `vscode` comes from the extension host.

Replace every `__...__` token in file contents with real extension identity,
repository/license metadata and **compatible exact tool versions**. Match
`engines.vscode` and `@types/vscode` to the oldest supported host; match Node
types to that host's embedded Node, not merely the build workstation. Do not
publish example metadata. Add the chosen license file. Generate a native lock
with the selected package manager after version selection; use frozen/locked
installation thereafter. No lock is fabricated for unresolved placeholders.

For a new npm-based fixture after substitution and dependency installation:

```sh
npm run typecheck
npm test
npm run package:files
npm run package
```

The source JSON-encodes each nonempty selected range in one edit/undo
transaction. The behavioral test runs in a real desktop extension host, checks
Unicode and escaping, checks one-step undo and checks that empty selections do
not edit. `test/extension.test.mjs` uses the project's installed
`@vscode/test-electron`. Set `VSCODE_TEST_VERSION` to the concrete host version,
or `VSCODE_EXECUTABLE_PATH` to an existing compatible host. Otherwise the
placeholder must be filled. Downloads and GUI/virtual-display requirements are
explicit; Node execution alone cannot test `vscode`. Temporary profiles are
isolated.

`test-host/index.cjs` exports the host runner entrypoint and assertions. Do not
replace that with a test that only asserts the host process launched. To test
the expected-result check, deliberately remove `JSON.stringify` in a disposable
copy and require the content assertion to fail, then restore it.

The declared trust/virtual-workspace support is appropriate only for this local
in-memory edit. Reassess it when adding workspace execution, filesystem access,
or external processes. Web support needs a separate browser entry and actual
web-host tests; do not claim it from a desktop VSIX.

Sources: [testing extension][upstream-source-1] and [extension
manifest][upstream-source-2]

[upstream-source-1]: https://code.visualstudio.com/api/working-with-extensions/testing-extension
[upstream-source-2]: https://code.visualstudio.com/api/references/extension-manifest
