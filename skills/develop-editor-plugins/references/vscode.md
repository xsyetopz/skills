# VS Code extensions

Gotchas for `package.json`, the extension host, tests, and `vsce`. Run
`bun scripts/check_vscode_manifest.mjs package.json --src src` first:
it encodes the manifest rules below as rule IDs `M001` to `M021`.

## Contents

- [Manifest and activation](#manifest-and-activation)
- [Commands and menus](#commands-and-menus)
- [Settings](#settings)
- [Documents and edits](#documents-and-edits)
- [Workspace Trust, virtual workspaces, and
  web](#workspace-trust-virtual-workspaces-and-web)
- [Secrets](#secrets)
- [Tests](#tests)
- [Bundling and packaging](#bundling-and-packaging)
- [Sources](#sources)

## Manifest and activation

- Mistake: raising `@types/vscode` past `engines.vscode`, or calling an
  API newer than the floor. Fix: pick the floor from the newest API the
  code calls and pin `@types/vscode` to the same minor. `vsce` refuses to
  package when the typings are newer, and newer APIs type-check but throw
  on older hosts. [vsce validation][vsce-validation]
- Mistake: `"engines": {"vscode": "*"}`. Fix: use a caret range such as
  `^1.74.0`. `vsce ls` accepts `*`, so only the checker (`M002`) catches it.
- Mistake: `"activationEvents": ["*"]` or `onStartupFinished` for a
  feature used on demand. Fix: declare nothing and let contributions
  activate the extension (implicit since 1.74), or list specific
  events. With a floor below 1.74, list `onCommand:<id>` for every
  command (`M016`). [activation events][activation]
- Mistake: a `contributes.commands` entry with no `registerCommand`, or a
  menu item naming an undeclared command. Fix: keep IDs identical in
  both places; `--src` reports `M015` and `M014`. VS Code only logs
  `Menu item references a command ... not defined`. [menus source][menus-src]
- Mistake: disposables created in `activate` and never pushed anywhere,
  so commands register twice after a window reload. Fix: push each to
  `context.subscriptions`, or to an owner with a shorter lifetime, and
  kill spawned processes in `deactivate`.
- Mistake: a manifest version such as `1.0.0-rc.1`. Fix: Marketplace
  takes `major.minor.patch` only; publish previews with
  `vsce package --pre-release` with a version that differs from the
  release (the docs suggest odd minors; `M004`, `M019`).
  [pre-release][pub-pre]
- Mistake: `icon` as SVG, more than 30 `keywords`, or a category outside
  the documented list. Fix: PNG icon, 30 keywords, documented category
  (`M005` to `M007`). [manifest fields][manifest]

## Commands and menus

- Mistake: hiding a risky command with a menu `when` clause. Fix: `when`
  only hides UI; the command stays callable from the palette, keybindings,
  and other extensions. Check the condition inside the handler. Hide a
  palette-only-by-mistake entry with `commandPalette` `when: "false"`.
- Mistake: a `when` key that nothing sets. Fix: `rg -n setContext src`
  for every custom key, and inspect values with **Developer: Inspect
  Context Keys**. [when clauses][when]

## Settings

- Mistake: one setting ID that is a prefix of another
  (`a.enable` and `a.enable.fast`), an unknown `scope`, or `$ref` in a
  schema. Fix: the Settings editor cannot render these (`M008` to `M010`).
  [configuration][config]
- Mistake: an executable path at `resource` or `window` scope. Fix: use
  `machine-overridable` so a cloned repo cannot set it, and list it in
  `restrictedConfigurations`.
- Mistake: caching `getConfiguration()` values at activation. Fix: read
  inside the handler, or listen to `onDidChangeConfiguration` and check
  `affectsConfiguration("section.key")`.

## Documents and edits

- Mistake: applying a result computed for document version N after an
  `await`. Fix: capture `document.version` (and a request counter)
  before the await and compare after; drop stale results. A host test
  cannot reproduce this race, so unit test the guard.
- Mistake: assuming `WorkspaceEdit` or `TextEditor.edit` saves the
  file. Fix: edits only dirty the buffer. Call `save()` only when the
  task says so. `onDidSaveTextDocument` and `onDidOpenTextDocument`
  also fire for settings and output documents; filter by language or URI.
- Mistake: editing inside `onDidSaveTextDocument`. Fix: use
  `onWillSaveTextDocument` with `event.waitUntil(Promise.resolve(edits))`
  so the edits land in the same save.
- Mistake: several `TextEditor.edit` calls for a multi-selection
  transform. Fix: one `edit` callback with all ranges is one undo step.
  Use one `workspace.applyEdit` for cross-range or cross-file edits.
- Mistake: `DocumentSelector` of bare language IDs. Fix: name the
  schemes, `{ language: "x", scheme: "file" }`. Without it the host logs
  `document selector without scheme` and providers run on git, output,
  and settings documents. [language features][langfeat]
- Mistake: stale diagnostics. Fix: `collection.set(uri, [])` or
  `delete` when the source changes or closes; dispose the collection.
- Mistake: `console.log` for extension logs. Fix: `createOutputChannel(name,
  { log: true })` gives levels and timestamps under the user's log-level
  setting.

## Workspace Trust, virtual workspaces, and web

- Mistake: declaring no `capabilities.untrustedWorkspaces`. Fix: without
  it the extension is disabled in Restricted Mode (`M021`). Declare
  `limited` with a description, and check `workspace.isTrusted` (and
  listen to `onDidGrantWorkspaceTrust`) before running workspace code.
  [Workspace Trust][trust]
- Mistake: reading an executable path from a setting with no
  `restrictedConfigurations`. Fix: list the key; in Restricted Mode the
  workspace value is ignored and `get` returns the default.
- Mistake: `uri.fsPath` and Node `fs` on every URI. Fix: only for
  `file` scheme; use `workspace.fs` otherwise. GitHub Repositories and
  vscode.dev use virtual schemes. Declare `virtualWorkspaces` with a
  description when a feature needs disk. [virtual workspaces][virtual]
- Mistake: adding `browser` while the bundle imports Node modules. Fix:
  a separate web entry that imports only `vscode`, built with esbuild
  `platform: "browser"` so a Node import fails the build. The web host
  ignores extensions that have only `main`. Keep shared code in a module
  with no `node:` imports. [web extensions][web]
- Mistake: assuming the extension runs on the UI machine. Fix: in SSH,
  container, and WSL windows a workspace extension runs remotely; set
  `extensionKind` only for a real reason, and check placement in
  **Developer: Show Running Extensions**. [extension host][host]

## Secrets

- Mistake: tokens in settings, `globalState`, logs, or `exports`. Fix:
  `context.secrets`. Test launches need `--use-inmemory-secretstorage`
  (older builds: `--disable-keytar`) to keep test secrets out of the OS
  keychain. Put these flags before the folder path: an unknown flag
  directly before the folder once kept it from opening.

## Tests

- Mistake: treating a unit test, `tsc`, or a built VSIX as proof of editor
  behavior. Fix: only a run in the extension host proves it. Keep pure
  logic in a module without `vscode` imports and unit test it with
  `bun test`; use `@vscode/test-cli` for the rest. [testing][testing]
- Mistake: running host tests against the user's own VS Code profile.
  Fix: let `@vscode/test-electron` download a build and pass private
  `--user-data-dir` and `--extensions-dir`. Keep that path short: macOS
  rejects IPC socket paths over 103 characters.
- Mistake: testing the oldest supported host only by reading docs. Fix:
  set `version` in `.vscode-test.mjs` to the engines floor and to
  `stable`, and run both.
- Mistake: testing Restricted Mode with a normal launch. Fix: launch
  the host directly on an untrusted folder (no
  `--disable-workspace-trust`), then assert the trust-gated command
  refuses.
  [test-cli][cli]

## Bundling and packaging

- Mistake: shipping `node_modules` and sources. Fix: bundle with esbuild
  (`external: ["vscode"]`), add `.vscodeignore`, and package with
  `--no-dependencies`. Inspect the list with `vsce ls --no-dependencies`
  before packaging. [bundling][bundling], [.vscodeignore][pub-ignore]
- Mistake: a `vscode:prepublish` script under Bun. Fix: `vsce` runs it
  with npm or Yarn; run the bundle script yourself, then
  `bunx vsce package --no-dependencies`.
- Mistake: installing the VSIX into the everyday profile to test it.
  Fix:
  `code --user-data-dir T/u --extensions-dir T/e --install-extension x.vsix`
  then list extensions in that profile.
- Mistake: native binaries in one universal VSIX. Fix: one VSIX per
  target with `vsce package --target <platform>`. [packaging][pub-package]
- Mistake: publishing, logging in, or creating a token as part of a
  check. Fix: stop at the VSIX unless the user asked to publish.
  [publishing][pub-auth]

## Sources

[activation]: https://code.visualstudio.com/api/references/activation-events
[bundling]: https://code.visualstudio.com/api/working-with-extensions/bundling-extension
[cli]: https://github.com/microsoft/vscode-test-cli/blob/main/README.md
[config]: https://code.visualstudio.com/api/references/contribution-points#contributes.configuration
[host]: https://code.visualstudio.com/api/advanced-topics/extension-host
[langfeat]: https://code.visualstudio.com/api/language-extensions/programmatic-language-features
[manifest]: https://code.visualstudio.com/api/references/extension-manifest
[menus-src]: https://github.com/microsoft/vscode/blob/main/src/vs/workbench/services/actions/common/menusExtensionPoint.ts
[pub-auth]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#publishing-extensions
[pub-ignore]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#using-.vscodeignore
[pub-package]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#packaging-extensions
[pub-pre]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#prerelease-extensions
[testing]: https://code.visualstudio.com/api/working-with-extensions/testing-extension
[trust]: https://code.visualstudio.com/api/extension-guides/workspace-trust
[virtual]: https://code.visualstudio.com/api/extension-guides/virtual-workspaces
[vsce-validation]: https://github.com/microsoft/vscode-vsce/blob/main/src/validation.ts
[web]: https://code.visualstudio.com/api/extension-guides/web-extensions
[when]: https://code.visualstudio.com/api/references/when-clause-contexts
