# Tests, bundling, packaging, and publishing

Cards for proving behavior and shipping a VSIX. Offline results come
from `sh assets/examples/verify.sh` (14 checks, Bun 1.4.2, Node 26.8.2,
TypeScript 7.0.2, esbuild 0.28.2, @vscode/vsce 4.0.0, macOS arm64). It
also passed with `HTTPS_PROXY=http://127.0.0.1:9` after one online run,
so a warm Bun cache is enough. Host results come from `verify.sh
network` (@vscode/test-cli 0.0.15, @vscode/test-electron 3.1.0).

## Contents

- [Unit tests for pure logic](#unit-tests-for-pure-logic)
- [Extension host tests with @vscode/test-cli][toc-1]
- [Direct extension host launch](#direct-extension-host-launch)
- [Bundling with esbuild](#bundling-with-esbuild)
- [.vscodeignore and vsce ls](#vscodeignore-and-vsce-ls)
- [vsce package and an isolated install](#vsce-package-and-an-isolated-install)
- [Pre-release and platform-specific packages][toc-2]
- [Manifest rule check](#manifest-rule-check)
- [Publishing prerequisites](#publishing-prerequisites)

## Unit tests for pure logic

**Definition.** Code that does not import `vscode` runs in any
JavaScript runtime, so `bun test` covers it in milliseconds without
downloading VS Code. Everything that touches the API needs the host
([testing extensions][testing]).

**Use when.**

- The logic is parsing, matching, edit computation, stale-result rules,
  or settings normalization. Move it to a module without `vscode`
  imports.

**Do not use when.**

- Claiming editor integration (activation, commands, diagnostics,
  edits). A unit test cannot load `vscode`.
- Mocking the whole `vscode` module to avoid host tests. The mocks
  encode assumptions the host does not share.

**Example.** `test/unit/core.test.ts` (excerpt):

```ts
import { expect, test } from "bun:test";
import { RequestGenerations } from "../../src/core";

test("rejects a superseded request at the same version", () => {
  const g = new RequestGenerations();
  const first = g.start("a");
  g.start("a");
  expect(g.isCurrent("a", first, 3, 3)).toBe(false);
});
```

**Cost removed.** A VS Code launch per logic change. Executed: `bun
test test/unit` reports `12 pass` in about 10 ms (machine-specific,
Bun's own timer). Removing the `(?!\()` lookahead from the TODO pattern
makes the suite fail.

**Verify.**

1. `bun test test/unit` shows `12 pass`, `0 fail`.
1. `rg -n 'from "vscode"' src/core.ts` prints nothing.

## Extension host tests with @vscode/test-cli

**Definition.** `vscode-test` (package `@vscode/test-cli`) reads
`.vscode-test.mjs` (`files`, `version`, `workspaceFolder`, `launchArgs`,
`env`, `mocha`, `useInstallation`). It downloads VS Code through
@vscode/test-electron unless `useInstallation.fromPath` is set, and runs
Mocha inside the Extension Development Host ([test-cli README][cli],
[config.cts][cli-config]).

**Use when.**

- Any claim about commands, activation, diagnostics, edits, settings,
  or secrets.

**Do not use when.**

- Testing Restricted Mode. `runTests()` always adds
  `--disable-workspace-trust` (next card).
- Running the tests in the user's running VS Code. The docs say CLI
  tests cannot run while another instance of the same version runs, so
  use a downloaded copy and a private `--user-data-dir`.
- Importing `suite`/`test` from a separate `mocha` dependency. The
  first run failed with `TypeError: Cannot read properties of undefined
  (reading 'describe')`. Use the globals from the Mocha that test-cli
  loads.

**Example.** `.vscode-test.mjs`:

```js
export default defineConfig({
  label: "trusted",
  files: "out/test/host/**/*.test.js",
  version: process.env.VSCODE_TEST_VERSION ?? "stable",
  ...(exe ? { useInstallation: { fromPath: exe } } : {}),
  workspaceFolder: `${tmp}/ws-t`,
  launchArgs: [
    "--use-inmemory-secretstorage",
    "--disable-keytar",
    `--user-data-dir=${tmp}/t/u`,
    `--extensions-dir=${tmp}/t/x`,
    "--disable-extensions",
  ],
  env: { GIT_CONFIG_GLOBAL: `${tmp}/gitconfig`, GIT_CONFIG_NOSYSTEM: "1" },
  mocha: { ui: "tdd", timeout: 20000 },
});
```

Keep `tmp` short. With a user-data dir under a long scratch path,
VS Code 1.139.1 failed with `IPC handle ".../1.13-main.sock" is longer
than 103 chars` and `listen EINVAL`. `mktemp -d` paths work.

**Cost removed.** Manual clicking in the Extension Development Host.
Executed: `6 passing` on VS Code 1.139.1 and on 1.74.0 (the engines
floor). A full `verify.sh network` run took about 48 s with the
download cached (machine-specific: this Mac, shared with other jobs).
A VS Code window opens during the run.

**Verify.**

1. `sh assets/examples/verify.sh network` prints `extension host
   (trusted): 6 passing`.
1. `VSCODE_TEST_VERSION=1.74.0 sh assets/examples/verify.sh network`
   prints `6 passing` on the floor, then exits 1 at the Restricted Mode
   step (`expected Restricted Mode`; see the next card).

## Direct extension host launch

**Definition.** VS Code runs extension tests when started with
`--extensionDevelopmentPath=<root>` and
`--extensionTestsPath=<module>`. The module exports `run(): Promise`,
and the process exits non-zero when the promise rejects
([testing][testing]). `runTests()` from @vscode/test-electron wraps
this launch and adds `--no-sandbox`, `--disable-gpu-sandbox`,
`--disable-updates`, `--skip-welcome`, `--skip-release-notes`,
`--no-cached-data`, and `--disable-workspace-trust` (read from
`out/runTest.js` 3.1.0).

**Use when.**

- The test needs a default that `runTests()` overrides, such as
  Restricted Mode.
- The test needs a pre-seeded profile (`User/settings.json`).

**Do not use when.**

- Running ordinary host tests. test-cli handles the download, Mocha,
  and reporting.

**Example.** From `verify.sh network`:

```sh
GIT_CONFIG_GLOBAL="$T/gitconfig" "$EXE" \
  --extensionDevelopmentPath="$EXT" \
  --extensionTestsPath="$EXT/out/test/untrusted/index.js" \
  --user-data-dir="$T/u/u" --extensions-dir="$T/u/x" \
  --disable-extensions --skip-welcome --skip-release-notes \
  --disable-updates --use-inmemory-secretstorage --disable-keytar \
  --no-sandbox --disable-gpu-sandbox "$T/ws-u"
```

`$T/u/u/User/settings.json` holds
`{"security.workspace.trust.startupPrompt": "never"}`.

**Cost removed.** An untested trust boundary. Executed (1.139.1):
`untrusted: 3 checks passed`. On 1.74.0 the same launch reported
`isTrusted === true` (cause not found).

**Verify.**

1. `verify.sh network` prints `extension host (Restricted Mode): 3
   checks passed`.
1. The process exits 0, and a failing assertion makes it exit 1.

## Bundling with esbuild

**Definition.** esbuild combines the entry and its imports into one
CommonJS file, with `vscode` marked external because the host provides
it. esbuild strips types without checking them, so `tsc --noEmit` runs
separately ([bundling][bundling]). The web host loads only one file per
extension.

**Use when.**

- The extension has more than one source file or has runtime
  dependencies. Always bundle a `browser` entry.

**Do not use when.**

- `vscode` is not external. esbuild fails with `Could not resolve
  "vscode"` (Executed), because `@types/vscode` has no runtime module.
- Code relies on `Function.prototype.name`. `--production` minifies
  names, so turn minification off for that code.

**Example.** `esbuild.mjs` (shared options):

```js
const common = {
  bundle: true,
  format: "cjs",
  minify: production,
  sourcemap: !production,
  sourcesContent: false,
  external: ["vscode"],
  logLevel: "warning",
};
```

Build with `bun esbuild.mjs --production` and type check with `bunx tsc
--noEmit -p .`.

**Cost removed.** Files loaded at activation and packaged. Executed:
the VSIX carries two JavaScript files, `dist/node/extension.js` (6.1 KB)
and `dist/web/extension.js` (5.36 KB), instead of the 5 modules that
`tsc` emits from `src/`.

**Verify.**

1. `grep -o 'require("[^"]*")' dist/node/extension.js | sort -u` lists
   only `vscode` and Node built-ins.
1. `bunx tsc --noEmit -p .` exits 0.

## .vscodeignore and vsce ls

**Definition.** `.vscodeignore` holds glob patterns, one per line, that
vsce leaves out of the VSIX; `!` negates a pattern. `vsce ls` prints
the files that would be packaged ([publishing][pub-ignore]). vsce
excludes `devDependencies` automatically. With `--no-dependencies`,
vsce skips dependency detection, which supports only npm and Yarn 1
([vsce README][vsce]).

**Use when.**

- Before every package. Sources, tests, maps, lockfiles, and build
  scripts do not belong in the VSIX.

**Do not use when.**

- Excluding a runtime file that the bundle does not contain (a WASM
  file, a native module, an `externals` dependency). Add a `!` pattern.
- Running `vsce ls` under Bun without `--no-dependencies`. vsce runs
  `npm list --production` to find dependencies (`out/npm.js`).

**Example.** `assets/examples/extension/.vscodeignore`:

```text
.vscode-test/**
.vscode-test.mjs
src/**
test/**
out/**
node_modules/**
esbuild.mjs
tsconfig*.json
bun.lock
**/*.map
*.vsix
```

**Cost removed.** Package size and leaked sources. Executed: `vsce ls
--no-dependencies` lists 5 files (`LICENSE`, `README.md`,
`package.json`, and the two bundles). With an empty ignore file it
lists 18, adding sources, tests, `bun.lock`, `tsconfig*.json`,
`esbuild.mjs`, and `.vscode-test.mjs`.

**Verify.**

1. `bunx vsce ls --no-dependencies` shows only runtime files.
1. Run `: >empty.ignore; bunx vsce ls --no-dependencies --ignoreFile
   empty.ignore`. The extra lines are what `.vscodeignore` removes.

## vsce package and an isolated install

**Definition.** `vsce package` validates the manifest and writes
`<name>-<version>.vsix`, a zip with `extension.vsixmanifest` and
`extension/`. `code --install-extension <file>` installs it
([publishing][pub-package]). vsce runs a `vscode:prepublish` script
through `npm run` or `yarn run` (`prepublish()` in `out/package.js`).

**Use when.**

- Testing the artifact that users receive, or distributing privately.

**Do not use when.**

- The project must stay on Bun and defines `vscode:prepublish`. vsce
  would call npm, so drop that script: build first, then package, as
  the fixture's `vsix` script does.
- Installing into the user's own profile to test. Always pass
  `--user-data-dir` and `--extensions-dir`.

**Example.**

```sh
bun esbuild.mjs --production
bunx vsce package --no-dependencies -o todo-owner.vsix </dev/null
code --user-data-dir "$P/u" --extensions-dir "$P/x" \
  --install-extension todo-owner.vsix
code --user-data-dir "$P/u" --extensions-dir "$P/x" \
  --list-extensions --show-versions
```

With stdin closed, vsce 4.0.0 printed warnings and continued, exiting
0. Missing `repository`: `Use --allow-missing-repository to bypass`.
Missing `LICENSE`: `LICENSE, LICENSE.md, or LICENSE.txt not found`.

**Cost removed.** Surprises that only the packaged form shows (a
missing bundle, an ignored asset). Executed: the VSIX has 7 zip
entries, and the private profile lists
`skills-example.todo-owner@0.2.0`.

**Verify.**

1. `unzip -l todo-owner.vsix` shows `extension/dist/...` for each entry
   in `main`/`browser`.
1. `--list-extensions --show-versions` on the private profile shows
   `<publisher>.<name>@<version>`.

## Pre-release and platform-specific packages

**Definition.** `vsce package --pre-release` marks the VSIX as a
pre-release and needs engines `>=1.63`. Versions stay
`major.minor.patch` and must differ from release versions; the docs
suggest odd minors for pre-releases. `--target <platform>` (VS Code
1.61+) builds one VSIX per platform: `win32-x64`, `win32-arm64`,
`linux-x64`, `linux-arm64`, `linux-armhf`, `alpine-x64`,
`alpine-arm64`, `darwin-x64`, `darwin-arm64`, `web`
([publishing][pub-pre]).

**Use when.**

- `--pre-release`: an opt-in channel for early builds.
- `--target`: native modules or platform binaries. Use `web` for the
  browser build of a platform-specific extension.

**Do not use when.**

- Putting a semver tag in `version` (`1.0.0-beta.1`). vsce 4.0.0
  packaged it, but the Marketplace does not support such tags (rule
  M004).
- Using `--target` for a pure JavaScript extension. One universal VSIX
  serves every platform.

**Example.**

```sh
bunx vsce package --no-dependencies --pre-release -o pre.vsix
bunx vsce package --no-dependencies --target web -o web.vsix
unzip -p pre.vsix extension.vsixmanifest | grep PreRelease
```

**Cost removed.** A second extension ID for previews. Executed:
`Microsoft.VisualStudio.Code.PreRelease` = `true`, and the web target
writes `TargetPlatform="web"`. With engines `^1.60.0`, vsce fails with
`Pre-release versions are supported by VS Code >=1.63`.

**Verify.**

1. `verify.sh` check `vsce package --pre-release sets ...PreRelease`.
1. `check_manifest.py package.json --pre-release` fires M019 below 1.63.

## Manifest rule check

**Definition.** [`scripts/check_manifest.py`](../scripts/check_manifest.py)
checks `package.json` against 21 documented rules (M001 to M021), each
linked to its source in `RULES`. `--src DIR` enables M015 (contributed
commands are passed to `registerCommand`), `--built` enables M018
(`main` and `browser` exist), and `--pre-release` enables M019. It
exits 0 when clean, 1 on errors, and 2 on unreadable input.

**Use when.**

- After every manifest edit, before packaging, and in CI.

**Do not use when.**

- Treating it as proof of behavior. It reads JSON and greps sources;
  host tests prove that the commands work.

**Example.**

```text
$ python3 scripts/check_manifest.py package.json --src src --built
0 error(s), 0 warning(s)
$ # after adding "todoOwner.enable.fast" next to "todoOwner.enable":
M008 error: setting `todoOwner.enable` is a full prefix of
`todoOwner.enable.fast`
```

**Cost removed.** Rules that vsce does not enforce. vsce 4.0.0 `ls`
accepted `engines.vscode: "*"` (M002), missing `onCommand` events on a
1.60 floor (M016), and a semver pre-release tag (M004). Executed:
`test_check_manifest.py` runs 27 tests; each rule fires on its
mutation, and the fixture is clean.

**Verify.**

1. `python3 scripts/test_check_manifest.py` prints `OK`.
1. `verify.sh` check `check_manifest.py: 0 error(s), 0 warning(s)`.

## Publishing prerequisites

**Definition.** Publishing to the Visual Studio Marketplace needs:

- a publisher, whose ID is fixed at creation and equals `publisher` in
  `package.json`;
- a unique `name` and `displayName`;
- credentials. Recommended: Microsoft Entra ID with workload identity
  federation and `vsce publish --azure-credential`. Alternative: a
  Personal Access Token with organization **All accessible
  organizations** and scope **Marketplace (Manage)**.

Azure DevOps retires global PATs on 2026-12-01 ([publishing][pub-auth]).
The vsce README on `main` documents `vsce publish --oidc` for GitHub
Actions, but `vsce publish --help` in 4.0.0 does not list it (checked
this session).

**Use when.**

- The user asked to publish and owns the publisher.

**Do not use when.**

- Nobody asked to publish. Stop at `vsce package`.
- The icon, README images, or badges are SVG from untrusted hosts, or
  README image URLs are not `https`. vsce refuses to publish.
- `keywords` exceed 30. The Marketplace rejects the upload.

**Example.** Commands for the user to run (not run here):

```sh
bunx vsce verify-pat skills-example     # checks PAT or Azure identity
bunx vsce publish --packagePath todo-owner.vsix --azure-credential
bunx vsce publish --pre-release --packagePath pre.vsix --pat "$VSCE_PAT"
```

A 401 or 403 on publish usually means that the PAT was created for one
organization or without **Marketplace (Manage)**.

**Cost removed.** Failed publish attempts and leaked tokens.
Not runnable here: the fixture has no publisher or credentials, and
`vsce publish` was not executed, by design.

**Verify.**

1. `bunx vsce verify-pat <publisher>` succeeds for the credential in
   use (user-run).
1. After publishing, `bunx vsce show <publisher>.<name>` lists the new
   version (user-run).

[testing]: https://code.visualstudio.com/api/working-with-extensions/testing-extension
[cli]: https://github.com/microsoft/vscode-test-cli/blob/main/README.md
[cli-config]: https://github.com/microsoft/vscode-test-cli/blob/main/src/config.cts
[bundling]: https://code.visualstudio.com/api/working-with-extensions/bundling-extension
[pub-ignore]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#using-.vscodeignore
[vsce]: https://github.com/microsoft/vscode-vsce/blob/main/README.md
[pub-package]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#packaging-extensions
[pub-pre]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#prerelease-extensions
[pub-auth]: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#publishing-extensions
[toc-1]: #extension-host-tests-with-vscodetest-cli
[toc-2]: #pre-release-and-platform-specific-packages
