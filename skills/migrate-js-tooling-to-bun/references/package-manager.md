# Package manager

Cards for moving installation, lockfiles, lifecycle scripts, workspaces,
and registries from npm, Yarn, or pnpm to Bun. "Executed" results come
from [`assets/examples/verify.sh`][verify] with Bun 1.4.2 and Node 26.8.2
on macOS arm64. The fixture is a two-package workspace with a `file:`
dependency whose `postinstall` writes `built.txt`.

## Contents

- [Responsibility inventory](#responsibility-inventory)
- [Bun version selection](#bun-version-selection)
- [Automatic lockfile migration](#automatic-lockfile-migration)
- [Resolution comparison](#resolution-comparison)
- [Binary lockfile conversion](#binary-lockfile-conversion)
- [Frozen installs in CI](#frozen-installs-in-ci)
- [Workspace edge gap](#workspace-edge-gap)
- [Lifecycle script trust](#lifecycle-script-trust)
- [Linker: hoisted or isolated](#linker-hoisted-or-isolated)
- [Registries, scopes, and credentials](#registries-scopes-and-credentials)

## Responsibility inventory

**Definition.** A table of who owns each responsibility before and after
the change: installation, lockfile, script runner, the runtime each
script actually starts, test runner, bundler, CI setup action, and
container base image. Moving one responsibility to Bun does not move
the others.

**Use when.** Before any edit. The request names the responsibilities
that move, for example "use bun install" or "run the server on Bun".

**Do not use when.** The request only asks about Bun performance; use
the `$optimize-javascript-code` skill.

**Example.**

```sh
rg -n '"packageManager"|"engines"|"workspaces"|"trustedDependencies"' \
  --glob 'package.json'
fd -H -t f '^(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|bun\.lockb?)$'
fd -H -t f '^(\.npmrc|\.nvmrc|\.node-version|\.tool-versions|bunfig\.toml)$'
rg -n 'npm (ci|install|run)|yarn|pnpm|setup-node|setup-bun|FROM node' \
  .github Dockerfile* 2>/dev/null
rg -n '"(start|test|build)":' --glob 'package.json'
```

| Job | Before | After | Evidence |
| --- | --- | --- | --- |
| install + lockfile | npm, `package-lock.json` | Bun, `bun.lock` | `bun ci` |
| `start` runtime | node | node (unchanged) | `start` prints node |
| tests | node:test | `bun test` | 3 pass |

**Cost removed.** An unrequested runtime or image change that would
otherwise surface only in production. The `start` output reports a
different runtime when it happens.

**Verify.**

1. Every row has an "after" owner, and each moved row names a command
   whose output proves the change.
1. Rows the request did not name keep their "before" owner.

## Bun version selection

**Definition.** The Bun executable that CI, containers, and developers
actually run. `packageManager: "bun@1.4.2"` in `package.json` records
the intended version but does not prove which executable ran.

**Use when.** Every migration, and every change to the Bun pin alone.

**Do not use when.** Never substitute "latest" for a version the user
named.

**Example.**

```sh
curl -fsSL https://bun.com/install | bash -s "bun-v1.4.2"
bun --version    # 1.4.2
bun --revision   # 1.4.2+50a8a8387
```

For a change to the pin alone, keep the dependency graph fixed: run
`bun ci`, then the tests. Never run `bun update` for a version change:
it resolves new dependency versions, so a failing test no longer points
at the runtime ([installation][installation]).

**Cost removed.** CI silently running a different Bun version from the
one tested locally.

**Verify.**

1. Each CI job and image prints `bun --version` and the output matches
   the pin.
1. After a change to the pin alone, `git diff --exit-code bun.lock`
   exits 0.

## Automatic lockfile migration

**Definition.** When no `bun.lock` exists, `bun install` converts these
lockfiles to `bun.lock`: `yarn.lock` v1, `package-lock.json` with
`lockfileVersion` 2, 3, or 4, and `pnpm-lock.yaml`. Bun keeps the
original file. It does not migrate `lockfileVersion` 1 (npm 6). For
that file it prints a warning and resolves from `package.json`, which
can change versions ([lockfile][lockfile]).

**Use when.** Installation moves and the repository has a supported
lockfile.

**Do not use when.** `bun.lock` already exists; the migration does not
run. With an npm v1 lockfile, upgrade it with npm first, or treat a
fresh resolution as a separate, reviewed decision.

**Example.** Executed on the fixture (`npm-project/`):

```text
$ bun install
+ native-dep@native-dep
3 packages installed [5.00ms]
Blocked 1 postinstall. Run `bun pm untrusted` for details.
$ ls
bun.lock  native-dep  node_modules  package-lock.json  package.json  packages
```

The migrated lockfile contains `"configVersion": 0`, so Bun keeps the
hoisted linker and npm's `node_modules` layout
([isolated installs][isolated]).

**Cost removed.** A full re-resolution that silently picks up new
transitive versions. The next card's comparison exposes any such
change.

**Verify.**

1. `bun.lock` exists and the old lockfile is still present.
1. Run the [resolution comparison](#resolution-comparison) before you
   delete the old lockfile.

## Resolution comparison

**Definition.** A per-package diff of resolved versions between the old
lockfile and `bun.lock`, produced by
[`scripts/compare_lockfiles.py`][compare]. Workspace and `file:` packages
compare as `link:<path>`. Exit status 0 means same, 1 means different,
and 2 means unreadable input.

**Use when.** After a migration, before removing the old lockfile, and
when reviewing any `bun.lock` change.

**Do not use when.** The old lockfile is Yarn or pnpm; the script reads
only `package-lock.json` v2/v3 and `bun.lock`. It also refuses graphs
that install one package at several versions
(`node_modules/a/node_modules/b`) or under a workspace folder
(`packages/x/node_modules/b`): it exits 2 with `nested install`, because
a per-name diff would hide changes. In both cases, diff the
`bun pm ls --all` output of the old tree (installed with its old tool)
against the new one.

**Example.** Executed:

```text
$ python3 scripts/compare_lockfiles.py package-lock.json bun.lock
same=3 added=0 removed=0 changed=0
```

A changed version prints `~ left-pad 1.3.0 -> 1.3.1` and exits 1. The
bundled tests cover the same, changed, added, nested, and unreadable
cases.

**Cost removed.** Unreviewed transitive upgrades in a migration,
counted by the `changed` lines.

**Verify.**

1. Exit status 0, or every `+`, `-`, and `~` line in the report is
   explained.
1. `python3 scripts/test_compare_lockfiles.py` passes (5 tests).

## Binary lockfile conversion

**Definition.** Bun before 1.2 wrote a binary `bun.lockb`. The
documented conversion to the text `bun.lock` is
`bun install --save-text-lockfile --frozen-lockfile --lockfile-only`,
after which you delete `bun.lockb` ([lockfile][lockfile]).

**Use when.** The repository has `bun.lockb` and every consumer runs Bun
1.2 or later.

**Do not use when.** A CI image or developer still runs Bun older than
1.2, the release that made `bun.lock` the default, unless you confirm
that release reads `bun.lock`.

**Example.**

```sh
cp bun.lockb /tmp/bun.lockb.saved
bun install --save-text-lockfile --frozen-lockfile --lockfile-only
bun pm ls --all > after.txt
```

Verification tier: not runnable here; Bun 1.4.2 has no fixture that
writes `bun.lockb`. Keep the saved copy until the comparison passes.

**Cost removed.** Unreadable lockfile diffs. A text `bun.lock` shows each
change as a line in `git diff`.

**Verify.**

1. `bun ci` passes with only `bun.lock` present.
1. `bun pm ls --all` output is identical before and after the
   conversion.

## Frozen installs in CI

**Definition.** `bun ci` is the same as
`bun install --frozen-lockfile`. It installs the versions from
`bun.lock`, never writes the lockfile, and fails when `package.json`
requires a lockfile change. Bun does not freeze the lockfile in CI on
its own ([install][install]).

**Use when.** Every CI install and container build after the migration.

**Do not use when.** Intentionally adding a dependency on a developer
machine.

**Example.** Executed. Adding `"extra": "file:./native-dep"` to
`package.json`:

```text
$ bun ci
error: lockfile had changes, but lockfile is frozen
note: try re-running without --frozen-lockfile and commit the updated lockfile
$ echo $?
1
```

`bun install --frozen-lockfile --dry-run` gives the same exit status 1
without installing.

**Cost removed.** CI builds that resolve versions other than the
reviewed lockfile's; `bun ci` fails instead of modifying `bun.lock`.

**Verify.**

1. The CI log shows `bun ci` or `--frozen-lockfile`.
1. On a copy, adding a dependency without updating the lockfile makes
   the CI install fail.

## Workspace edge gap

**Definition.** `bun ci` does not detect a new `workspace:*` dependency
between two workspace packages. The install succeeds and `bun.lock`
stays unchanged, even though the lockfile lists each workspace's
dependencies.

**Use when.** A workspace repository gates CI on a frozen install.

**Do not use when.** The repository has no workspaces.

**Example.** Executed. Adding
`"dependencies": {"@fixture/app": "workspace:*"}` to
`packages/util/package.json`:

```text
$ bun ci; echo $?
0
$ bun install --lockfile-only && git diff --exit-code bun.lock
+      "dependencies": {
+        "@fixture/app": "workspace:*",
+      },
```

Use this CI check:

```sh
bun ci
bun install --lockfile-only
git diff --exit-code bun.lock
```

**Cost removed.** Stale committed lockfiles, which the next developer's
install rewrites inside an unrelated change.

**Verify.**

1. `verify.sh` shows `bun ci` passing and `--lockfile-only` changing
   `bun.lock` for the same edit.

## Lifecycle script trust

**Definition.** Bun runs lifecycle scripts (`preinstall`,
`postinstall`) only for trusted packages, as set by
`trustedDependencies` in `package.json`:

- Field omitted: a built-in list of popular npm packages.
- A list of names: only those packages, and the built-in list is
  ignored.
- `[]`: no packages.

Packages from `file:`, `link:`, `git:`, or `github:` sources must be
listed explicitly, even when their name is on the built-in list
([lifecycle][lifecycle]).

**Use when.** A dependency builds native code or downloads binaries in
`postinstall`, such as `sharp`, `esbuild`, or a local addon.

**Do not use when.** You have not read the blocked package's script. A
package in `trustedDependencies` runs arbitrary code at install time.

**Example.** Executed:

```text
$ bun pm untrusted
./node_modules/native-dep @native-dep
 » [postinstall]: node -e "require('fs').writeFileSync('built.txt','ok')"
$ bun pm trust native-dep
 ✓ [postinstall]: node -e "require('fs').writeFileSync('built.txt','ok')"
```

`package.json` now contains `"trustedDependencies": ["native-dep"]`.
Creating the field turns off the built-in list, so also add every
built-in package you still need, such as `esbuild`.

**Cost removed.** Installs that succeed without their build output: a
missing `.node` binary, or `built.txt` absent before trust.

**Verify.**

1. `bun pm untrusted` lists nothing that the project needs.
1. The build output exists, for example `node_modules/native-dep/built.txt`.
1. A command that loads the addon succeeds.

## Linker: hoisted or isolated

**Definition.** A hoisted install flattens packages into the root
`node_modules`, as npm and Yarn do. An isolated install places packages
in `node_modules/.bun` and links each package only to its declared
dependencies, as pnpm does. The default depends on the lockfile's
`configVersion`:

- 1 with workspaces: isolated.
- 1 without workspaces: hoisted.
- 0: hoisted.

A migration from npm or Yarn writes 0. A migration from pnpm writes 1
([isolated installs][isolated]).

**Use when.** Isolated: to expose undeclared (phantom) imports.
Hoisted: to keep npm's layout while only the package manager moves.

**Do not use when.** Treating isolated as proof that imports are
declared. The root `node_modules` still exposes root dependencies and
workspace packages, and the `node_modules/.bun/node_modules` fallback
exposes the rest unless `install.hoist = false` is set.

**Example.** Executed. A fresh workspace gets `configVersion: 1` and
`node_modules/.bun`, yet `packages/app` can still import `native-dep`,
which only the root declares. The strict setting:

```toml
# bunfig.toml
[install]
linker = "isolated"
hoist = false
```

**Cost removed.** Packages that import undeclared dependencies and
break when published or moved; the strict setting turns this into an
import error.

**Verify.**

1. Record `configVersion` from `bun.lock` and the linker in the report.
1. Run each workspace's tests from the workspace's own directory.

## Registries, scopes, and credentials

**Definition.** Bun reads `.npmrc` and `[install]` / `[install.scopes]`
in `bunfig.toml`. Registry values can reference environment variables
([scopes and registries][scopes], [.npmrc][npmrc]).

**Use when.** The project installs from a private registry or scope.

**Do not use when.** Never write a token literal into a committed
file, and never switch a scope to the public registry to get past an
authentication error.

**Example.**

```toml
[install.scopes]
"@example" = { token = "$NPM_TOKEN", url = "https://registry.example.test/" }
```

Verification tier: not runnable here (no private registry). The
fixture has no registry dependencies.

**Cost removed.** Installs that pull a same-named public package
instead of the private one, and leaked tokens.

**Verify.**

1. `rg -n 'npm_[A-Za-z0-9]{36}|_authToken=[^$]' .npmrc bunfig.toml`
   finds nothing.
1. `bun.lock` lists the private registry URL for each scoped package.

[verify]: ../assets/examples/verify.sh
[compare]: ../scripts/compare_lockfiles.py
[installation]: https://bun.com/docs/installation
[lockfile]: https://bun.com/docs/pm/lockfile
[install]: https://bun.com/docs/pm/cli/install
[lifecycle]: https://bun.com/docs/pm/lifecycle
[isolated]: https://bun.com/docs/pm/isolated-installs
[scopes]: https://bun.com/docs/pm/scopes-registries
[npmrc]: https://bun.com/docs/pm/npmrc
