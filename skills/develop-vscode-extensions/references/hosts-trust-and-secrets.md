# Hosts, Workspace Trust, virtual workspaces, web, and secrets

Cards for where the extension runs and what it may do there. Host results
come from `sh assets/examples/verify.sh network` (VS Code 1.139.1 and
1.74.0 downloaded by @vscode/test-electron 3.1.0, macOS arm64).

## Contents

- [untrustedWorkspaces capability](#untrustedworkspaces-capability)
- [Trust guard in code](#trust-guard-in-code)
- [restrictedConfigurations](#restrictedconfigurations)
- [virtualWorkspaces capability and URI handling][toc-1]
- [Web extension: the browser entry](#web-extension-the-browser-entry)
- [Separate Node, browser, and common modules][toc-2]
- [extensionKind placement](#extensionkind-placement)
- [SecretStorage](#secretstorage)

## untrustedWorkspaces capability

**Definition.** `capabilities.untrustedWorkspaces.supported` in
`package.json` takes three values:

- `true`: the extension runs unchanged in Restricted Mode;
- `false`: it stays disabled until the user trusts the workspace;
- `"limited"`: it runs, and its code disables trust-sensitive features.

`false` and `"limited"` need a `description`. An extension with a
`main` and no declaration counts as `false` ([Workspace Trust][trust]).

**Use when.**

- `true`: the extension never treats workspace content as code or as
  execution settings (themes, grammars, pure text transforms).
- `"limited"`: some features execute workspace-controlled code, paths,
  or settings (running a tool, loading workspace `node_modules`).
- `false`: nothing useful works without execution (a debugger front
  end for workspace scripts).

**Do not use when.**

- `true` while any code path spawns a workspace-configured executable.
  Restricted Mode then no longer protects the user.
- Debug adapters and task providers that use only the built-in flows.
  VS Code already blocks debugging and tasks in Restricted Mode, so the
  guide recommends `true` for them.

**Example.**

```json
"capabilities": {
  "untrustedWorkspaces": {
    "supported": "limited",
    "description": "Reading the owner from git runs an executable.",
    "restrictedConfigurations": ["todoOwner.gitPath"]
  }
}
```

**Cost removed.** Extensions disabled in every untrusted folder because
they declared nothing (rule M021 warns), or enabled with an execution
path open (a review item). Executed (host, 1.139.1): the fixture
activates in Restricted Mode and serves diagnostics while the git
command refuses.

**Verify.**

1. `check_manifest.py` exits 0 (M011 shape, M012 settings, M021).
1. `verify.sh network` check `extension host (Restricted Mode): 3
   checks passed`.

## Trust guard in code

**Definition.** `workspace.isTrusted` (typings since 1.56) is `true`
when the user trusted the workspace. `onDidGrantWorkspaceTrust` fires
when trust is granted later. The `isWorkspaceTrusted` context key hides
UI ([Workspace Trust][trust]).

**Use when.**

- A handler executes something the workspace controls. Check
  `isTrusted` at the moment it runs.
- Registration-time work needs trust (starting a server). Wait for
  `onDidGrantWorkspaceTrust`.

**Do not use when.**

- Hiding the menu entry is the only guard. Commands still run through
  `executeCommand` and keybindings.
- Reading `isTrusted` once at activation and caching it. The user can
  grant trust later in the session.

**Example.** `src/extension.node.ts`:

```ts
vscode.commands.registerCommand(
  "todoOwner.ownerFromGit",
  async (): Promise<string | undefined> => {
    if (!vscode.workspace.isTrusted) {
      log.warn("ownerFromGit refused: workspace is not trusted");
      return undefined;
    }
    // ... run git with the folder as cwd
  },
),
```

**Cost removed.** Code execution from a cloned repository before the
user decides to trust it. Executed (host, 1.139.1):
`executeCommand("todoOwner.ownerFromGit")` returns `undefined` in
Restricted Mode and `"Test Owner"` in a trusted run.

Harness facts: `runTests()` in @vscode/test-electron 3.1.0 always adds
`--disable-workspace-trust` (`out/runTest.js`). Restricted Mode
therefore needs a direct launch (`<Code> --extensionDevelopmentPath=...
--extensionTestsPath=... <folder>`) with a profile whose settings hold
`"security.workspace.trust.startupPrompt": "never"`. That gave
`isTrusted === false` on 1.139.1. On 1.74.0 the same launch reported
`isTrusted === true` (cause not found), so Restricted Mode is verified
on 1.139.1 only. No test exercised `onDidGrantWorkspaceTrust`.

**Verify.**

1. Run `rg -n 'execFile|spawn|exec\(' src` and check that each call
   site is reached only after an `isTrusted` check.
1. `verify.sh network`: the untrusted run and the trusted test
   `trusted: ownerFromGit runs git and stores the owner` both pass.

## restrictedConfigurations

**Definition.** With `"limited"`, setting IDs listed in
`untrustedWorkspaces.restrictedConfigurations` return only user-defined
values in Restricted Mode, and workspace values are withheld. Granting
trust fires a configuration change event ([Workspace Trust][trust]).

**Use when.**

- A setting holds an executable path, command-line flags, or a script
  that a malicious repository could set in `.vscode/settings.json`.

**Do not use when.**

- The settings only select presentation (colors, severity).
  Restricting them just ignores the user's workspace preferences.

**Example.** The Restricted Mode test workspace contains
`.vscode/settings.json` with `{"todoOwner.gitPath":
"/nonexistent/evil-git"}`, and `test/untrusted/index.ts` asserts:

```ts
const config = vscode.workspace.getConfiguration("todoOwner");
assert.equal(config.get("gitPath"), "git");
assert.equal(config.inspect<string>("gitPath")?.workspaceValue, undefined);
```

**Cost removed.** Trust checks in code for each setting. Executed
(host, 1.139.1): `get` returns the default `git` while the file on disk
holds the evil path, and `inspect().workspaceValue` is also
`undefined`.

**Verify.**

1. `check_manifest.py` M012: every restricted ID is a declared setting.
1. The `verify.sh network` Restricted Mode run passes.

## virtualWorkspaces capability and URI handling

**Definition.** `capabilities.virtualWorkspaces` declares support for
workspaces backed by a file system provider (for example
`vscode-vfs://github/...`). Values: `true` (the default when absent),
`false`, or `{ "supported": "limited", "description": ... }`. VS Code
sets the `virtualWorkspace` context key when all folders are virtual
([virtual workspaces][virtual]).

**Use when.**

- `true`: all file access goes through `workspace.fs` and URIs.
- `"limited"`: some features need a local disk (tools, `fsPath`). Hide
  them with `!virtualWorkspace` or `resourceScheme == file`.
- `false`: the core feature needs a local disk.

**Do not use when.**

- Using `uri.fsPath` on a non-`file` URI. It is valid only for `file`.
- Using Node `fs` for workspace files. Use `workspace.fs`, which
  delegates to the provider.

**Example.**

```json
"virtualWorkspaces": {
  "supported": "limited",
  "description": "Reading the owner from git needs a local folder."
}
```

```ts
// src/extension.node.ts: pick a local folder for the git command.
const folder = vscode.workspace.workspaceFolders?.find(
  (f) => f.uri.scheme === "file",
);
// src/core.ts, unit tested:
export function isVirtualWorkspace(schemes: readonly string[]): boolean {
  return schemes.length > 0 && schemes.every((s) => s !== "file");
}
```

**Cost removed.** `ENOENT` errors and broken features in GitHub
Repositories and vscode.dev windows. Executed (unit): the
`isVirtualWorkspace` tests. Not executed (not attempted): a real
virtual workspace needs the GitHub Repositories extension and a
signed-in GitHub account. The user runs **Open GitHub Repository...**
and invokes each command.

**Verify.**

1. Run `rg -n 'fsPath|from "node:fs"|require\("fs"\)' src` and check
   that a `file` scheme check guards each use.
1. `check_manifest.py` M013 (shape and description).

## Web extension: the browser entry

**Definition.** The `browser` field names the entry for the web
extension host, which is a browser WebWorker. Constraints: one bundled
file; `require` only for `vscode`; no Node globals (`process`, `path`,
...); no child processes; workspace and storage access only through
`workspace.fs`; network only through `fetch`, with CORS. An extension
is a web extension when it has `browser`, or when it has no `main` and
none of `localizations`, `debuggers`, `terminal`,
`typescriptServerPlugins` ([web extensions][web]).

**Use when.**

- The extension should work in vscode.dev, github.dev, and Codespaces
  in the browser.

**Do not use when.**

- The feature needs a process or a native module. Keep it in the
  `main` entry and register a stub in the web entry.
- Pointing `browser` at a file that imports Node modules. Bundling for
  `platform: "browser"` fails.

**Example.** `src/extension.web.ts`:

```ts
import * as vscode from "vscode";
import { type TodoOwnerApi, activateCommon, settingOwner } from "./common";

export function activate(context: vscode.ExtensionContext): TodoOwnerApi {
  const log = vscode.window.createOutputChannel("TODO Owner", { log: true });
  context.subscriptions.push(
    log,
    vscode.commands.registerCommand("todoOwner.ownerFromGit", () => {
      void vscode.window.showInformationMessage(
        "Reading git is not available in the browser.",
      );
      return undefined;
    }),
  );
  return activateCommon(context, log, async (doc) => settingOwner(doc));
}
```

**Cost removed.** Absence from the web Extensions view: the web host
ignores extensions that have only `main`. Executed: the web bundle's
only `require` is `vscode`; `vsce package` writes the tag
`__web_extension` into `extension.vsixmanifest`; and
`esbuild --platform=browser` on the Node entry fails with
`Could not resolve "node:child_process"`. Not executed in this session:
a browser run, `bunx @vscode/test-web
--extensionDevelopmentPath=. --browserType=chromium .`, which downloads
VS Code for the Web and a Playwright browser.

**Verify.**

1. `verify.sh` checks `web only vscode` and `__web_extension`.
1. Desktop web host: run `code --extensionDevelopmentPath=.
   --extensionDevelopmentKind=web`, then **Developer: Show Running
   Extensions** lists the extension under the web host.

## Separate Node, browser, and common modules

**Definition.** Three module groups. `common` imports only `vscode` and
pure code. `node/` may import Node built-ins. Each entry
(`extension.node.ts`, `extension.web.ts`) wires the common code to its
host-specific parts ([web extensions][web]).

**Use when.**

- One extension ships both `main` and `browser`.

**Do not use when.**

- The extension is web-only or Node-only. One entry is simpler.
- Choosing an implementation at run time (`typeof process`) inside one
  bundle. The browser bundle still fails to resolve the Node imports.

**Example.** `esbuild.mjs` builds both entries:

```js
await esbuild.build({
  ...common,
  entryPoints: ["src/extension.node.ts"],
  platform: "node",
  target: "node16",
  outfile: "dist/node/extension.js",
});
await esbuild.build({
  ...common,
  entryPoints: ["src/extension.web.ts"],
  platform: "browser",
  target: "es2022",
  outfile: "dist/web/extension.js",
});
```

**Cost removed.** Node imports that leak into the web bundle. Executed:
the Node bundle requires `node:child_process` and `vscode`, and the web
bundle requires only `vscode`.

**Verify.**

1. `grep -o 'require("[^"]*")' dist/web/extension.js | sort -u` prints
   only `require("vscode")`.
1. `rg -n 'from "node:' src --glob '!src/node/**'` prints nothing.

## extensionKind placement

**Definition.** `extensionKind` sets where a Node extension runs in
remote setups, in preference order: `["workspace"]` next to the files
(SSH, container, WSL, Codespaces), `["ui"]` on the local machine, or
both. An extension that runs on Node and in the browser gets a Node
host when one is available. Web-only extensions ignore `extensionKind`
([extension host][host]).

**Use when.**

- `["workspace"]`: the extension reads workspace files or runs tools
  there (most extensions).
- `["ui", "workspace"]`: the extension needs no workspace access, and
  running locally avoids installing it on each remote.

**Do not use when.**

- The extension is web-only. The docs recommend leaving the field
  unset.
- `["ui"]` while reading workspace files through Node `fs`. The files
  are on the remote machine.

**Example.** The fixture omits the field, and vsce records the derived
value `Microsoft.VisualStudio.Code.ExtensionKind` = `workspace,web` in
`extension.vsixmanifest` (Executed).

```json
{ "extensionKind": ["workspace"] }
```

**Cost removed.** Tools that run on the wrong machine in remote
windows. Not executed (not attempted): this needs a remote (SSH,
container, WSL). In a remote window, **Developer: Show Running
Extensions** shows the host.

**Verify.**

1. `unzip -p <name>.vsix extension.vsixmanifest | grep ExtensionKind`.
1. In a remote window, the running-extensions view lists the extension
   under the intended host.

## SecretStorage

**Definition.** `context.secrets` (typings since 1.53) stores strings
encrypted and unsynced. Methods: `store`, `get`, `delete`,
`onDidChange`, and `keys()` (typings since 1.105). Desktop uses
Electron `safeStorage`; the web uses a Double Key Encryption
implementation ([common capabilities][storage]).

**Use when.**

- Storing tokens, passwords, or API keys.

**Do not use when.**

- The state is not secret. Use `workspaceState`/`globalState`
  mementos, or `storageUri`/`globalStorageUri` for large files.
- Storing secrets in settings. `settings.json` is plain text and can
  sync.
- Logging the value or returning it to other extensions.

**Example.** `src/common.ts`:

```ts
await context.secrets.store(TOKEN_KEY, token);
log.info("API token stored"); // never log the value
// ...
await context.secrets.delete(TOKEN_KEY);
// API for tests and other extensions exposes presence only:
hasApiToken: async () =>
  (await context.secrets.get(TOKEN_KEY)) !== undefined,
```

**Cost removed.** Plain-text tokens in settings or globalState.
Executed (host): after a store, `hasApiToken() === true`; after a
delete, `false`. Test launches pass `--use-inmemory-secretstorage`
(current [argv.ts][argv]) and `--disable-keytar` (its name in 1.74.0)
to keep secrets out of the OS keychain. Put these flags first: on
1.74.0, with the then-unknown `--use-inmemory-secretstorage` right
before the folder path, the folder did not open (observed; 2 host tests
failed).

**Verify.**

1. Host test `SecretStorage round trip through the extension API`
   passes.
1. Run `rg -n 'secrets\.(get|store)' src` and check that no result
   reaches a log call or `exports`.

[trust]: https://code.visualstudio.com/api/extension-guides/workspace-trust
[virtual]: https://code.visualstudio.com/api/extension-guides/virtual-workspaces
[web]: https://code.visualstudio.com/api/extension-guides/web-extensions
[host]: https://code.visualstudio.com/api/advanced-topics/extension-host
[storage]: https://code.visualstudio.com/api/extension-capabilities/common-capabilities#data-storage
[argv]: https://github.com/microsoft/vscode/blob/main/src/vs/platform/environment/node/argv.ts
[toc-1]: #virtualworkspaces-capability-and-uri-handling
[toc-2]: #separate-node-browser-and-common-modules
