# Manifest, activation, commands, and settings

Cards for `package.json` and the code that binds to it. The runnable
extension is [`assets/examples/extension/`][ext]. `Executed` results come
from [`assets/examples/verify.sh`][verify] on macOS arm64 with Bun 1.4.2,
Node 26.8.2, TypeScript 7.0.2, and @vscode/vsce 4.0.0. `network` mode ran
the host suite in VS Code 1.139.1 and 1.74.0, downloaded by
@vscode/test-electron 3.1.0.

## Contents

- [Extension manifest](#extension-manifest)
- [Engines floor and @types/vscode pin](#engines-floor-and-typesvscode-pin)
- [Explicit activation events](#explicit-activation-events)
- [Implicit activation from contributions][toc-1]
- [activate, deactivate, and context.subscriptions][toc-2]
- [Commands: registration and contribution][toc-3]
- [When clauses and enablement](#when-clauses-and-enablement)
- [Custom context keys with setContext](#custom-context-keys-with-setcontext)
- [Configuration contribution](#configuration-contribution)
- [Reading and updating settings](#reading-and-updating-settings)

## Extension manifest

**Definition.** `package.json` at the extension root. `name`, `version`,
`publisher`, and `engines.vscode` are required. `main` names the Node
entry and `browser` the web entry. `contributes` declares UI, and
`capabilities` declares trust and virtual-workspace support
([manifest][manifest]). The extension ID is `<publisher>.<name>`.

**Use when.**

- Creating an extension, or changing contributions, entries, or
  capabilities.

**Do not use when.**

- Storing runtime state or user data. The manifest is read-only at
  runtime; use settings or the storage APIs.

**Example.** Excerpt of the fixture manifest (full file:
`assets/examples/extension/package.json`):

```json
{
  "name": "todo-owner",
  "version": "0.2.0",
  "publisher": "skills-example",
  "engines": { "vscode": "^1.74.0" },
  "main": "./dist/node/extension.js",
  "browser": "./dist/web/extension.js",
  "activationEvents": [],
  "categories": ["Linters"]
}
```

These rules fail silently or late, and
[`scripts/check_manifest.py`](../scripts/check_manifest.py) encodes all
of them: `name` lowercase without spaces; `engines.vscode` not `*`; at
most 30 `keywords`; `categories` from the documented list; `icon` not
SVG ([publishing][pub-constraints]); version `major.minor.patch` only.

**Cost removed.** Manifest errors found at load or publish time.
Executed: `check_manifest.py` reports 0 findings on the fixture and
fires each of its 21 rules on a targeted mutation
(`test_check_manifest.py`, 27 tests). vsce 4.0.0 `ls` accepted
`engines.vscode: "*"`, so vsce alone misses that rule.

**Verify.**

1. `python3 scripts/check_manifest.py package.json --src src --built`
   prints `0 error(s), 0 warning(s)` and exits 0.
1. `bunx vsce ls --no-dependencies` exits 0 (vsce's own manifest checks).

## Engines floor and @types/vscode pin

**Definition.** `engines.vscode` (`^1.74.0`) is the oldest VS Code that
may install the extension ([compatibility][compat]). `@types/vscode`
decides which APIs type-check. vsce refuses to package when the
`@types/vscode` major.minor is greater than the engines floor
([vsce validation.ts][vsce-validation]).

**Use when.**

- Choosing the floor. Take the newest API the code calls and find the
  first `@types/vscode` minor that declares it. From a grep of the
  newest patch of every minor from 1.40 to 1.138: `SecretStorage` 1.53,
  `workspace.isTrusted` 1.56, `TextDocumentChangeEvent.reason` 1.62,
  `LogOutputChannel` 1.74 (1.74.0 compiles the fixture, 1.73.1 does
  not), `TextDocument.encoding` 1.100, `SecretStorage.keys()` 1.105.
- Raising the floor to adopt an API. Raise both values together.

**Do not use when.**

- Setting `@types/vscode` to latest with an old floor. Newer APIs
  type-check, then throw on old hosts, and vsce rejects the package.
- Pinning `@types/node` to the build machine's Node. The host embeds its
  own: VS Code 1.74.0's `.nvmrc` says `16.14` ([1.74.0 .nvmrc][nvmrc]),
  so the fixture pins `@types/node` 16.18.126.

**Example.**

```json
{
  "engines": { "vscode": "^1.74.0" },
  "devDependencies": {
    "@types/node": "16.18.126",
    "@types/vscode": "1.74.0"
  }
}
```

TypeScript 7.0.2 rejects `"moduleResolution": "Node"` with `TS5108 ...
node10 has been removed`, so the fixture uses `Node16` (Executed).

**Cost removed.** Runtime `TypeError`s on the oldest supported host.
Executed: with `@types/vscode@1.73.1`, `tsc --noEmit` fails with
`TS2724: '"vscode"' has no exported member named 'LogOutputChannel'`.
With `@types/vscode` 1.138.0 and `^1.74.0`, vsce prints `@types/vscode
1.138.0 greater than engines.vscode ^1.74.0`.

**Verify.**

1. `bun add -d @types/vscode@<floor-1>`, then `bunx tsc --noEmit -p .`
   must fail on the API that set the floor (verify.sh check 1).
1. `VSCODE_TEST_VERSION=1.74.0 sh verify.sh network` runs the trusted
   host suite on the floor (Executed: `6 passing` on 1.74.0). The script
   then exits 1 at the Restricted Mode step with `AssertionError
   [ERR_ASSERTION]: expected Restricted Mode`, because `isTrusted`
   stayed `true` on 1.74.0 (cause not found).

## Explicit activation events

**Definition.** Strings in `activationEvents` that load the extension
when the event fires. `activate()` runs once, on the first one
([activation events][activation]). Examples: `onLanguage:python`,
`workspaceContains:**/.editorconfig`, `onFileSystem:sftp`,
`onUri`, `onStartupFinished`, `*`.

**Use when.**

- The trigger is not a contribution: a file in the workspace
  (`workspaceContains`), a URI scheme (`onFileSystem`), a URI handler
  (`onUri`), or a webview to restore (`onWebviewPanel`).
- Background work must start after startup without blocking it.
  `onStartupFinished` fires after all `*` extensions finish activating.

**Do not use when.**

- A contribution implies the event and the floor is 1.74+ (next card).
- `*`. It activates at startup, and the docs allow it only when no other
  combination works. vsce 4.0.0 prints `WARNING Using '*' activation is
  usually a bad idea` (Executed; exit status stays 0).

**Example.**

```json
{
  "activationEvents": [
    "workspaceContains:**/.todo-owner.json",
    "onStartupFinished"
  ]
}
```

**Cost removed.** Extension load and `activate()` time in sessions that
never use the feature. Observe it in **Developer: Show Running
Extensions** (activation time and event per extension) or in
`<user-data-dir>/logs/<session>/window1/exthost/exthost.log`, which logs
`ExtensionService#_doActivateExtension <id>, startup: <bool>,
activationEvent: '<event>'`.

**Verify.**

1. `rg -n '"\*"' package.json` finds no `*` in `activationEvents`.
1. In a host run, `grep _doActivateExtension exthost.log` shows
   `startup: false` and the intended event.

## Implicit activation from contributions

**Definition.** Since VS Code 1.74.0, contributed commands, languages,
views, custom editors, and authentication providers activate the
extension without `onCommand`/`onLanguage`/`onView`/`onCustomEditor`/
`onAuthenticationRequest` entries. Contributed tasks do so since 1.76.0
([activation events][activation]). vsce accepts `"activationEvents": []`
with `main` only when the floor is `>=1.74`.

**Use when.**

- The `engines.vscode` floor is 1.74.0 or later, and the trigger is a
  contributed command, language, view, custom editor, or auth provider.

**Do not use when.**

- The floor is below 1.74. List `onCommand:<id>` for every user-facing
  command, or the command fails with "command not found" on old hosts
  ([commands guide][commands]). `check_manifest.py` rule M016 enforces
  this.
- The command is internal, called only by the extension itself through
  `executeCommand`. It needs no contribution at all.

**Example.** Excerpt from the fixture's `package.json`, which has 7
commands and no activation events:

```json
{
  "activationEvents": [],
  "contributes": {
    "commands": [
      {
        "command": "todoOwner.encodeJsonStrings",
        "title": "Encode Selections as JSON Strings",
        "category": "TODO Owner",
        "enablement": "editorHasSelection && !editorReadonly"
      }
    ]
  }
}
```

**Cost removed.** Stale `onCommand` lists that drift from
`contributes.commands`. Executed (host, VS Code 1.139.1 and 1.74.0):
`isActive` is `false` before the first command and `true` after, and
`exthost.log` records `activationEvent:
'onCommand:todoOwner.clearApiToken'` although the manifest lists none.

**Verify.**

1. Host test `implicit activation: inactive until a command runs` in
   `test/host/trusted.test.ts` passes.
1. `grep "activationEvent: 'onCommand:" exthost.log` shows the command.

## activate, deactivate, and context.subscriptions

**Definition.** The entry module exports `activate(context)`, called
once. Its return value becomes `extension.exports`. `deactivate()` runs
on shutdown and must return a Promise for async cleanup
([activation events][activation]). Every `Disposable` pushed to
`context.subscriptions` is disposed on deactivation, but async `dispose`
functions are not awaited ([vscode.d.ts][dts]).

**Use when.**

- Registering anything that returns a `Disposable`: commands,
  providers, event listeners, diagnostic collections, output channels.

**Do not use when.**

- A shorter lifetime owns the resource (one panel, one document, one
  request). Dispose it there, or it lives until the window closes.
- Child processes. Disposing a registration does not kill a spawned
  process; track and kill it yourself.

**Example.** `src/extension.node.ts` (excerpt):

```ts
export function activate(context: vscode.ExtensionContext): TodoOwnerApi {
  const log = vscode.window.createOutputChannel("TODO Owner", { log: true });
  context.subscriptions.push(log);
  // ... registerCommand results are pushed the same way
  return activateCommon(context, log, async (doc) => settingOwner(doc));
}

export function deactivate(): void {
  // Everything is in context.subscriptions; nothing async to await.
}
```

**Cost removed.** Duplicate listeners and leaked registrations after
reload. Observe: after **Developer: Reload Window**, each TODO has one
diagnostic (not two) and no "command already exists" error appears.

**Verify.**

1. Run `rg -n 'register|onDid|onWill|create' src` and confirm each
   result is pushed to `context.subscriptions` or disposed by its owner.
1. Host test `SecretStorage round trip through the extension API` reads
   `getExtension(id).exports`, which proves the `activate` return value.

## Commands: registration and contribution

**Definition.** `commands.registerCommand(id, handler)` binds an ID to a
function. `contributes.commands` gives it a title, category, icon, and
`enablement`, and shows it in the Command Palette ([commands][commands]).
`executeCommand` returns the handler's return value.

**Use when.**

- User-facing actions (palette, keybinding, menu): register and
  contribute with the same ID.
- Programmatic entry points for tests or other extensions: register;
  contributing is optional.

**Do not use when.**

- Contributing without registering. Invoking the command fails with
  "command not found". Rule M015 greps sources for
  `registerCommand("<id>"`.
- Hiding a dangerous command from menus as its only protection. It
  still runs through `executeCommand` and keybindings, so check in the
  handler ([trust guide][trust]).

**Example.**

```json
{
  "command": "todoOwner.addOwnerToAll",
  "title": "Add Owner to All TODOs",
  "category": "TODO Owner",
  "icon": "$(person-add)"
}
```

```ts
context.subscriptions.push(
  vscode.commands.registerCommand(
    "todoOwner.addOwnerToAll",
    async (): Promise<boolean> => {
      const document = vscode.window.activeTextEditor?.document;
      if (!document) return false;
      // ... apply a WorkspaceEdit, return whether it applied
      return true;
    },
  ),
);
```

**Cost removed.** Contributed but unregistered IDs (M015), and menu
items that point at undeclared commands, which VS Code reports as `Menu
item references a command ... not defined in the 'commands' section`
([menusExtensionPoint.ts][menus-src]; rule M014).

**Verify.**

1. `python3 scripts/check_manifest.py package.json --src src` exits 0.
1. A host test calls `executeCommand("<id>")` and asserts the returned
   value or the resulting document text.

## When clauses and enablement

**Definition.** A `when` clause on a menu item hides the item. A
command's `enablement` disables the command in every menu and
keybinding: the Command Palette drops disabled commands, and context
menus grey them out ([commands][commands], [when clauses][when]).
Operators: `!`, `&&`, `||`, `==`, `!=`, `=~`, `<`, `>`, `in`, `not in`.
`config.<setting>` reads a setting.

**Use when.**

- `enablement`: the action needs a state (`editorHasSelection &&
  !editorReadonly`).
- `menus.commandPalette` `when`: hide a command outside its context,
  or use `"when": "false"` for commands that need arguments.
- Trust or host restrictions: `isWorkspaceTrusted`, `virtualWorkspace`,
  `isWeb`, `resourceScheme == file`.

**Do not use when.**

- The clause is meant as a security boundary (see the Commands card).
- A comparison has no spaces. `foo<1` is invalid; write `foo < 1`.

**Example.**

```json
"menus": {
  "commandPalette": [
    { "command": "todoOwner.addOwner", "when": "false" },
    {
      "command": "todoOwner.ownerFromGit",
      "when": "isWorkspaceTrusted && !virtualWorkspace && !isWeb"
    }
  ],
  "editor/title": [
    {
      "command": "todoOwner.addOwnerToAll",
      "when": "todoOwner.hasFindings",
      "group": "navigation"
    }
  ]
}
```

**Cost removed.** Palette entries that fail when chosen. Inspect values
with **Developer: Inspect Context Keys**, which prints them in the
Developer Tools console.

**Verify.**

1. Every `menus.*.command` is contributed (`check_manifest.py`, M014).
1. Manual: in a Restricted Mode window, the palette does not list
   **Use Git User Name as Default Owner** (not executed: manual UI).

## Custom context keys with setContext

**Definition.** `executeCommand("setContext", key, value)` publishes a
context key for `when` and `enablement`. Array and object values work
with `in`/`not in` ([when clauses][when]).

**Use when.**

- UI depends on extension state (findings exist, a server is running).

**Do not use when.**

- A built-in key already holds the state (`editorLangId`,
  `resourceScheme`, `isWorkspaceTrusted`).
- The key has no prefix. Use `<extension>.<name>` to avoid collisions.

**Example.** `src/common.ts`:

```ts
const refreshContext = (): void => {
  const uri = vscode.window.activeTextEditor?.document.uri;
  const count = uri ? (diagnostics.get(uri)?.length ?? 0) : 0;
  void vscode.commands.executeCommand(
    "setContext",
    "todoOwner.hasFindings",
    count > 0,
  );
};
```

**Cost removed.** Title-bar actions that show when they do nothing.

**Verify.**

1. Run `rg -n 'setContext' src` and check that a `when` uses each key.
1. Manual: **Developer: Inspect Context Keys** shows
   `todoOwner.hasFindings: true` on a file with an unowned TODO.

## Configuration contribution

**Definition.** `contributes.configuration.properties` declares setting
IDs with JSON-schema `type`, `default`, `enum`, `description`, and
`scope` (`application`, `machine`, `machine-overridable`, `window`
(default), `resource`, `language-overridable`) ([configuration][config]).

**Use when.**

- The user or workspace must change behavior without code changes.
- Values differ per folder in multi-root workspaces: `scope:
  "resource"`.
- Values are executable paths or machine-specific: `machine-overridable`
  or `machine`. These scopes are not synced.

**Do not use when.**

- The schema needs `$ref`/`definitions`. They are unsupported, so
  schemas must be self-contained.
- One ID is a full prefix of another (`a.b` and `a.b.c`). This is not
  allowed.
- The value is a secret. Settings are plain JSON; use SecretStorage.

**Example.**

```json
"todoOwner.severity": {
  "type": "string",
  "enum": ["error", "warning", "information", "hint"],
  "default": "warning",
  "scope": "resource",
  "description": "Severity of the TODO diagnostic."
}
```

**Cost removed.** Settings that the Settings editor cannot render, and
machine paths that sync to other machines. Rules M008 to M010 catch
prefix IDs, unknown scopes, and `$ref`.

**Verify.**

1. `check_manifest.py` exits 0.
1. Host test `diagnostics follow edits and the severity setting`
   updates the setting and observes the new severity.

## Reading and updating settings

**Definition.** `workspace.getConfiguration(section, scope)` returns a
`WorkspaceConfiguration`:

- `get(key, default)` resolves the effective value for that scope;
- `inspect(key)` returns `defaultValue`, `globalValue`,
  `workspaceValue`, `workspaceFolderValue`, and language values;
- `update(key, value, target)` writes to `Global`, `Workspace`, or
  `WorkspaceFolder`, and `undefined` removes the value
  ([vscode.d.ts][dts]).

`onDidChangeConfiguration` delivers an event with
`affectsConfiguration(section, scope?)`.

**Use when.**

- Reading at use time, with the document as scope so folder settings
  apply: `getConfiguration("todoOwner", document)`.
- Reacting to changes. Filter with `affectsConfiguration("todoOwner")`.

**Do not use when.**

- Caching values at activation. They go stale when settings change.
- Calling `update` with `WorkspaceFolder` for a `window`-scoped setting,
  or with no folder open. It throws.

**Example.** `src/common.ts`:

```ts
const config = vscode.workspace.getConfiguration(SECTION, document);
const severity = SEVERITY[parseSeverity(config.get("severity"))];
// ...
vscode.workspace.onDidChangeConfiguration((e) => {
  if (!e.affectsConfiguration(SECTION)) return;
  vscode.workspace.textDocuments.forEach(relint);
});
```

`parseSeverity` maps unknown hand-edited values to `"warning"` (unit
tested).

**Cost removed.** A reload to apply settings. Executed (host): after
`update("severity", "error", Global)`, the diagnostic severity becomes
`Error` without a reload, and the log shows `configuration changed;
relinting open documents`.

**Verify.**

1. Host test `diagnostics follow edits and the severity setting` passes.
1. `rg -n 'getConfiguration\(' src` shows a scope argument wherever the
   setting is `resource`-scoped.

[ext]: ../assets/examples/extension/
[verify]: ../assets/examples/verify.sh
[manifest]: https://code.visualstudio.com/api/references/extension-manifest
[pub-constraints]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#publishing-extensions
[compat]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#visual-studio-code-compatibility
[vsce-validation]: https://github.com/microsoft/vscode-vsce/blob/main/src/validation.ts
[nvmrc]: https://github.com/microsoft/vscode/blob/1.74.0/.nvmrc
[activation]: https://code.visualstudio.com/api/references/activation-events
[commands]: https://code.visualstudio.com/api/extension-guides/command
[trust]: https://code.visualstudio.com/api/extension-guides/workspace-trust
[menus-src]: https://github.com/microsoft/vscode/blob/main/src/vs/workbench/services/actions/common/menusExtensionPoint.ts
[when]: https://code.visualstudio.com/api/references/when-clause-contexts
[config]: https://code.visualstudio.com/api/references/contribution-points#contributes.configuration
[dts]: https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.d.ts
[toc-1]: #implicit-activation-from-contributions
[toc-2]: #activate-deactivate-and-contextsubscriptions
[toc-3]: #commands-registration-and-contribution
