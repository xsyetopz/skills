# Package manager

Sources: [installation](https://bun.com/docs/installation),
[lockfile](https://bun.com/docs/pm/lockfile), [install](https://bun.com/docs/pm/cli/install),
[lifecycle](https://bun.com/docs/pm/lifecycle), [isolated
installs](https://bun.com/docs/pm/isolated-installs), [scopes and
registries](https://bun.com/docs/pm/scopes-registries), [.npmrc](https://bun.com/docs/pm/npmrc).

## Contents

- [Version pin](#version-pin)
- [Lockfile migration](#lockfile-migration)
- [Resolution comparison](#resolution-comparison)
- [Binary lockfile](#binary-lockfile)
- [Frozen installs](#frozen-installs-and-the-workspace-gap)
- [Lifecycle script trust](#lifecycle-script-trust)
- [Linker](#linker)
- [Registries and credentials](#registries-and-credentials)

## Version pin

- `packageManager: "bun@X"` records intent but does not prove which executable ran. Print
  `bun --version` and `bun --revision` in every CI job and image, and match the version the user
  named. Never substitute "latest".
- For a change to the pin alone, run `bun ci` and the tests, and confirm
  `git diff --exit-code bun.lock`. `bun update` resolves new versions, so a failing test no longer
  points at the runtime.

## Lockfile migration

- With no `bun.lock`, `bun install` converts `yarn.lock` v1, `package-lock.json` with
  `lockfileVersion` 2, 3, or 4, and `pnpm-lock.yaml`, and keeps the original file.
- It does not migrate `lockfileVersion` 1 (npm 6): it warns and resolves from `package.json`, which
  can change versions. Upgrade that lockfile with npm first, or treat fresh resolution as a separate
  reviewed decision.
- If `bun.lock` already exists, no migration runs.
- A migration from npm or Yarn writes `"configVersion": 0`, which keeps the hoisted layout.

## Resolution comparison

- Before deleting the old lockfile, run
  `python3 scripts/compare_lockfiles.py package-lock.json bun.lock` and explain every changed line.
  Exit 2 means nested versions or bad input; diff `bun pm ls --all` from each side instead.
- The script reads only `package-lock.json`. For Yarn or pnpm, diff the old tool's full resolved
  list against `bun pm ls --all`.

## Binary lockfile

- Bun before 1.2 wrote a binary `bun.lockb`. Convert with
  `bun install --save-text-lockfile --frozen-lockfile --lockfile-only`, then delete `bun.lockb`,
  only after checking `bun --version` in each CI image and the user confirming developers run Bun
  1.2 or later.
- Keep a saved copy until `bun ci` passes with only `bun.lock` and `bun pm ls --all` is identical
  before and after.

## Frozen installs and the workspace gap

- `bun ci` is `bun install --frozen-lockfile`: it never writes the lockfile and exits 1 with
  "lockfile had changes, but lockfile is frozen" when `package.json` needs a change. Bun does not
  freeze on its own in CI.
- `bun ci` does not detect a new `workspace:*` dependency between two workspace packages; it exits 0
  and `bun.lock` stays stale. In workspace repositories add:

```sh
bun ci
bun install --lockfile-only
git diff --exit-code bun.lock
```

## Lifecycle script trust

- Bun runs `preinstall`/`postinstall` only for trusted packages. `trustedDependencies` omitted means
  a built-in list of popular packages; a list of names means only those, and the built-in list is
  ignored; `[]` means none. Packages from `file:`, `link:`, `git:`, or `github:` always need an
  explicit entry.
- `Blocked N postinstall` or a missing `.node` binary: run `bun pm untrusted` and read each script.
  Show the list and stop for the user's approval before `bun pm trust NAME`, which runs that
  package's lifecycle scripts at once. Creating the field switches off the built-in list, so also
  list every built-in package you still need (for example `esbuild`, `sharp`).
- Verify the build output exists and a command that loads the addon works.

## Linker

- Hoisted flattens into the root `node_modules` (npm, Yarn); isolated uses `node_modules/.bun` and
  links only declared dependencies (pnpm). Default by `configVersion`: 1 with workspaces is
  isolated, 1 without is hoisted, 0 is hoisted. A pnpm migration writes 1.
- Isolated does not prove imports are declared: root dependencies, workspace packages, and a
  `node_modules/.bun/node_modules` fallback stay visible. For strict checking use
  `linker = "isolated"` and `hoist = false` under `[install]` in `bunfig.toml`.
- Record `configVersion` and the linker in the report, and run each workspace's tests from its own
  directory.

## Registries and credentials

- Bun reads `.npmrc` and `[install.scopes]` in `bunfig.toml`; values can reference environment
  variables:

```toml
[install.scopes]
"@example" = { token = "$NPM_TOKEN", url = "https://registry.example.test/" }
```

- Never write a token literal into a committed file, and never move a scope to the public registry
  to get past an authentication error. Check:
  `rg -l -e '_authToken=[^$]' -e 'token\s*=\s*"[^$]' .npmrc bunfig.toml` lists no file (`-l` keeps
  the token out of output), and `bun.lock` lists the private URL for scoped packages.
