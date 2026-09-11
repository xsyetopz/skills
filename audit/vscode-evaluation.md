# VS Code extension evaluation

Evaluated on 2026-09-12. The skill remains explicit-only. Nine overlapping
reference fragments were consolidated into two coherent references after review.

## Corrections

- Replaced the greeting starter and trivial helper test with a selection-editing
  command and real extension-host assertions. Nonempty selections become JSON
  string literals in one undo transaction; empty selections remain unchanged.
- Awaited the editor edit result and retained registration disposal. The browser
  entrypoint shares the platform-only implementation, without runtime Bun or
  Node imports.
- Removed fake asynchronous hover scaffolding and unconditional persisted schema
  versioning. Real asynchronous providers still require cancellation and stale
  result handling.
- Preserved the configured checks. The test gate now builds and runs the actual
  host, rather than dropping tests when the greeting helper was removed.

## Desktop and packaging evidence

The instantiated starter used Bun 1.4.2, Biome 2.5.13, TypeScript 7.0.2,
`@types/vscode` 1.137.0, `@types/node` 22.19.15, `@vscode/test-electron` 3.1.0,
and vsce 3.9.2. The installed desktop host was VS Code 1.137.0.

`bun run check` passed configured Biome checks, strict TypeScript checks, the
real desktop extension-host test, and build validation. No diagnostic rules were
weakened. Destructuring environment variables satisfied both TypeScript index
signature access and Biome literal-key requirements.

The host test checks exact output for Unicode, quotes, backslashes, multiple
selections, a single undo, and an all-empty selection with no document change.
An intentionally incorrect first assertion made the real host exit with failure;
the fixture was restored before the full check. Temporary profiles isolate user
state. Built-in account and deprecation warnings were retained, not suppressed.

vsce built a six-file VSIX containing package metadata, license, and both
compiled entrypoints, without source, tests, or node_modules. Both manifest
entrypoints resolve in the archive. The real Code CLI installed it into an
isolated profile. The installed payload was then loaded through
`--extensionDevelopmentPath` and passed the command test. This is packaged-code
execution, not proof of every normal installed-extension activation path.

Evidence artifacts:

- `/tmp/vscode-check.log`
- `/tmp/vscode-skill-evidence/host-test.log`
- `/tmp/vscode-skill-evidence/mutant.log`
- `/tmp/vscode-package-evidence.vsix`
- `/tmp/vscode-packaged-test.log`

## Browser evidence

The actual Chromium web host ran VS Code 1.137.0, commit
`645f29cc3176500b4b5762ba887cf2a7f0ffdf2c`, through `@vscode/test-web` 0.0.81.
The same assertions used a temporary browser-compatible strict equality helper
instead of Node's assertion import. The command loaded `dist/browser.js` and
passed every assertion. Replacing the first actual value with `MUTANT` produced
a failed assertion and runner exit 1; the fixture was restored.

The successful invocation used `--coi`, without disabling browser security, and
placed the test module beneath the extension development directory. The runner
serves tests relative to that directory. Earlier launches without cross-origin
isolation returned exit 0 without executing the test. Therefore a zero exit code
alone was rejected as evidence: explicit start/pass markers, module requests,
and a failing negative control establish actual execution.

Logs are `/tmp/vscode-web-evidence/run-coi.log` and
`/tmp/vscode-web-evidence/run-mutant.log`. The temporary web adapter is
evaluation infrastructure, not a second production implementation.

## Source checks and limits

The current [publishing documentation][publishing] confirms Entra publishing,
`--azure-credential`, publisher Contributor access, and the announced global PAT
retirement date of 2026-12-01. No publisher credentials were used and nothing
was published.

Desktop untitled-document tests do not establish remote-host behavior, Workspace
Trust execution guards, or webview security. Those need feature-specific checks
when implemented. Browser command execution does not establish every virtual
filesystem contract.

Both skill validators passed. Source/package validation does not substitute for
host behavior, independent forward testing, or the full repository goal audit.

[publishing]:
  https://code.visualstudio.com/api/working-with-extensions/publishing-extension
