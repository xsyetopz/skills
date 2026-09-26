---
name: develop-vscode-extensions
description: >-
  Builds, tests, and packages VS Code extensions: manifest, activation,
  commands, edits, diagnostics, language providers, Workspace Trust, web
  builds, vsce. Use when writing or fixing a VS Code extension. Not for Visual
  Studio or standalone language servers.
---

# Develop VS Code Extensions

Change a VS Code extension so that the manifest, the code, and the
packaged VSIX agree, and prove each claim in the host that runs it.
Each card in the references gives the definition, **Use when** and
**Do not use when** conditions, the cost it removes, verification, and a
runnable example from `assets/examples/extension/` (a TODO-owner linter
with Node and browser entries).

## Workflow

1. Inspect before editing: `package.json` (`engines.vscode`, `main`,
   `browser`, `activationEvents`, `contributes`, `capabilities`,
   `@types/vscode`), the lockfile and package manager, the build script,
   `.vscodeignore`, and existing tests. Run
   `rg -n 'registerCommand|register\w+Provider|createOutputChannel' src`.
1. Fix the engines floor from the newest API the change calls and pin
   `@types/vscode` to it ([floor card][floor]). Do not raise the floor
   unless the user accepts dropping older VS Code versions.
1. Implement with the card that matches the task (table below). Keep
   logic that does not need `vscode` in its own module.
1. Check the manifest: `python3 scripts/check_manifest.py package.json
   --src src` ([manifest rules][rules]).
1. Type check and unit test: `bunx tsc --noEmit -p .` and `bun test`
   (or the project's own runner).
1. Run host tests with `@vscode/test-cli` in a downloaded VS Code with
   a private profile ([host tests][hosttests]). Test Restricted Mode
   with a direct launch ([direct launch][direct]).
1. Bundle, then `bunx vsce ls --no-dependencies`, `bunx vsce package
   --no-dependencies`, and install the VSIX into a private profile
   ([vsce ls][ls], [package][package]).
1. Report with the completion evidence below.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| New extension, manifest fields, Marketplace rules | [Extension manifest](references/manifest-and-activation.md#extension-manifest) |
| "Property does not exist on vscode", old hosts crash | [Engines floor](references/manifest-and-activation.md#engines-floor-and-typesvscode-pin) |
| Extension never loads / loads at startup | [Explicit activation](references/manifest-and-activation.md#explicit-activation-events), [implicit activation](references/manifest-and-activation.md#implicit-activation-from-contributions) |
| `command 'x' not found` | [Commands](references/manifest-and-activation.md#commands-registration-and-contribution), [implicit activation](references/manifest-and-activation.md#implicit-activation-from-contributions) |
| Leaks or duplicates after reload | [activate and subscriptions](references/manifest-and-activation.md#activate-deactivate-and-contextsubscriptions) |
| Menu item shows when it cannot work | [When clauses](references/manifest-and-activation.md#when-clauses-and-enablement), [setContext](references/manifest-and-activation.md#custom-context-keys-with-setcontext) |
| New setting, per-folder values | [Configuration contribution](references/manifest-and-activation.md#configuration-contribution) |
| Setting change ignored until reload | [Reading settings](references/manifest-and-activation.md#reading-and-updating-settings) |
| Result applied to text that changed | [Version and dirty](references/documents-and-language-features.md#textdocument-version-and-dirty-state), [stale guard](references/documents-and-language-features.md#stale-asynchronous-result-guard) |
| Edit written to disk unexpectedly, or not saved | [Edit versus save](references/documents-and-language-features.md#edit-versus-save) |
| Format or fix on save | [onWillSaveTextDocument](references/documents-and-language-features.md#pre-save-edits-with-onwillsavetextdocument) |
| Multi-range or cross-file edit | [WorkspaceEdit](references/documents-and-language-features.md#workspaceedit-and-workspaceapplyedit) |
| Transform selections | [TextEditor.edit](references/documents-and-language-features.md#texteditoredit-for-selection-edits) |
| Problems view entries | [DiagnosticCollection](references/documents-and-language-features.md#diagnosticcollection) |
| Hover, completion, quick fix, formatting | [Providers](references/documents-and-language-features.md#language-feature-providers), [selectors](references/documents-and-language-features.md#document-selectors-with-schemes) |
| "document selector without scheme" in the log | [Selectors with schemes](references/documents-and-language-features.md#document-selectors-with-schemes) |
| Logging, log levels | [LogOutputChannel](references/documents-and-language-features.md#logoutputchannel) |
| Runs tools or workspace code | [untrustedWorkspaces](references/hosts-trust-and-secrets.md#untrustedworkspaces-capability), [trust guard](references/hosts-trust-and-secrets.md#trust-guard-in-code) |
| Executable path in settings | [restrictedConfigurations](references/hosts-trust-and-secrets.md#restrictedconfigurations) |
| GitHub Repositories, vscode.dev, `fsPath` errors | [virtualWorkspaces](references/hosts-trust-and-secrets.md#virtualworkspaces-capability-and-uri-handling) |
| Must work in the browser | [browser entry](references/hosts-trust-and-secrets.md#web-extension-the-browser-entry), [split modules](references/hosts-trust-and-secrets.md#separate-node-browser-and-common-modules) |
| SSH, container, WSL placement | [extensionKind](references/hosts-trust-and-secrets.md#extensionkind-placement) |
| Tokens and passwords | [SecretStorage](references/hosts-trust-and-secrets.md#secretstorage) |
| Fast tests of logic | [Unit tests](references/test-bundle-publish.md#unit-tests-for-pure-logic) |
| Tests of editor behavior | [test-cli](references/test-bundle-publish.md#extension-host-tests-with-vscodetest-cli), [direct launch](references/test-bundle-publish.md#direct-extension-host-launch) |
| Slow activation, many files, web build | [esbuild](references/test-bundle-publish.md#bundling-with-esbuild) |
| VSIX too large or missing files | [.vscodeignore and vsce ls](references/test-bundle-publish.md#vscodeignore-and-vsce-ls) |
| Ship a VSIX, try it locally | [vsce package](references/test-bundle-publish.md#vsce-package-and-an-isolated-install) |
| Preview channel, native binaries | [Pre-release and targets](references/test-bundle-publish.md#pre-release-and-platform-specific-packages) |
| Publish to the Marketplace | [Publishing prerequisites](references/test-bundle-publish.md#publishing-prerequisites) |

## Rules

- Every contributed command is registered with the same ID, and every
  menu item names a contributed command. `check_manifest.py --src`
  proves both.
- The engines floor and `@types/vscode` move together. vsce refuses to
  package when the typings are newer than the floor.
- With a floor below 1.74, list `onCommand:<id>` for every user-facing
  command. Never use `*` activation when a specific event exists.
- Push every disposable to `context.subscriptions` or to the owner with
  the shorter lifetime. Kill spawned processes yourself.
- Revalidate `document.version` (and a request generation) after every
  `await` before writing an edit or diagnostic.
- Edits do not save. Save only when the task says so, and filter save
  and open events by selector: they fire for settings files too.
- Provider selectors name their schemes. Use `uri.fsPath` and Node `fs`
  only for `file` URIs; otherwise use `workspace.fs`.
- Anything that runs workspace-controlled code or paths checks
  `workspace.isTrusted` in the handler. Menu `when` clauses are not a
  security boundary. List risky settings in `restrictedConfigurations`.
- The `browser` bundle imports nothing but `vscode`. Bundle it with
  `platform: "browser"` so that Node imports fail the build.
- Secrets go to `context.secrets`, never to settings, mementos, logs,
  or `exports`.
- Host tests never use the user's running VS Code or profile: download
  a build, pass private `--user-data-dir` and `--extensions-dir`, keep
  that path short (macOS rejects IPC socket paths over 103 characters),
  and pass `--use-inmemory-secretstorage --disable-keytar` first, or at
  least not directly before the folder path (1.74 knows only the second,
  and the unknown flag right before the folder path kept the folder from
  opening).
- A unit test, a type check, or a built VSIX does not prove editor
  behavior. Only a host test does. Say which tier each claim reached.
- Under Bun, do not define `vscode:prepublish` (vsce runs it with npm or
  Yarn) and pass `--no-dependencies` to vsce after bundling.
- Do not publish, log in, or create tokens unless the user asked.

## Bundled tools

- `scripts/check_manifest.py PACKAGE_JSON [--src DIR] [--built]
  [--pre-release]` checks the documented manifest rules and exits 0,
  1 (errors), or 2 (unreadable). Tests:
  `scripts/test_check_manifest.py`.
- `assets/examples/extension/` is the reference extension: `src/core.ts`
  (pure logic), `src/common.ts` (shared API code),
  `src/extension.node.ts` and `src/extension.web.ts` (entries),
  `test/unit/`, `test/host/`, `test/untrusted/`, `.vscode-test.mjs`,
  `esbuild.mjs`, `.vscodeignore`, and a `bun.lock`.
- `sh assets/examples/verify.sh` runs the offline checks in a temporary
  copy (a warm Bun cache is enough). `sh assets/examples/verify.sh
  network` downloads VS Code (`VSCODE_TEST_VERSION`, default `stable`)
  and runs the host suites; a VS Code window opens while it runs.

## References

- [Manifest and activation](references/manifest-and-activation.md):
  manifest, engines floor, activation events, lifecycle, commands, when
  clauses, context keys, configuration, and reading settings.
- [Documents and language features][docs-ref]:
  version and dirty state, edit versus save, pre-save edits,
  WorkspaceEdit, TextEditor.edit, the stale-result guard, diagnostics,
  selectors, providers, and LogOutputChannel.
- [Hosts, trust, and secrets](references/hosts-trust-and-secrets.md):
  Workspace Trust, restrictedConfigurations, virtual workspaces, the
  web entry, module split, extensionKind, and SecretStorage.
- [Test, bundle, publish](references/test-bundle-publish.md): unit and
  host tests, direct launch, esbuild, `.vscodeignore`, vsce packaging,
  pre-release and targets, the manifest checker, and publishing.

## Completion evidence

The final report contains:

- The VS Code floor (`engines.vscode`), the `@types/vscode` pin, and the
  host kinds the extension claims (desktop, remote, web).
- `check_manifest.py` output, type-check output, and unit test counts.
- Host test output with the VS Code version it ran on, or the exact
  reason it could not run and the command the user runs instead.
- For packaging: the `vsce ls` file list, the VSIX name, and the
  private-profile install listing.
- Each claim labeled Executed, Compiled, or Not runnable here; trust,
  web, and remote behavior stated separately.

[floor]: references/manifest-and-activation.md#engines-floor-and-typesvscode-pin
[hosttests]: references/test-bundle-publish.md#extension-host-tests-with-vscodetest-cli
[direct]: references/test-bundle-publish.md#direct-extension-host-launch
[ls]: references/test-bundle-publish.md#vscodeignore-and-vsce-ls
[package]: references/test-bundle-publish.md#vsce-package-and-an-isolated-install
[rules]: references/test-bundle-publish.md#manifest-rule-check
[docs-ref]: references/documents-and-language-features.md
