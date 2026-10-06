---
name: migrate-js-to-bun
description: >-
  Moves npm, Yarn, and pnpm installs, lockfiles, Node scripts, Jest and node test suites,
  and esbuild bundles to Bun with the same resolved versions and test counts.
  Use when adopting bun install, bun test, or bun build in an existing project.
  Not for speeding up a Bun app or tsc type checking.
disable-model-invocation: true
---

# Migrate JS to Bun

Move only the responsibilities the request names (package manager, script runtime, test runner,
bundler) and keep the resolved dependency graph, build output, test coverage, and runtime equal
unless it says otherwise.

## Rules

- Moving the package manager does not move the runtime. `bun run` keeps a script's `node` command on
  Node; add `--bun` only when the request moves the runtime. Confirm the runtime once with
  `bun -e 'console.log(process.versions.bun)'`, because a `--bun` in CI silently switches
  production.
- Run `bun install` with the old lockfile present so Bun converts it, then
  `python3 scripts/compare_lockfiles.py package-lock.json bun.lock` and explain every change before
  deleting the old lockfile. A fresh resolution can move versions unnoticed, and `bun update` or
  deleting the lockfile to get past an error hides that.
- Replace CI installs with `bun ci` (`bun install --frozen-lockfile`). In workspaces also run
  `bun install --lockfile-only` then `git diff --exit-code bun.lock`, because `bun ci` misses a new
  `workspace:*` edge and exits 0.
- npm `lockfileVersion` 1 is not migrated and `bun.lockb` needs
  `bun install --save-text-lockfile --frozen-lockfile --lockfile-only` (after checking
  `bun --version` in each CI image and the user confirming developers run Bun 1.2 or later). See
  [Package manager](references/package-manager.md#lockfile-migration).
- Bun skips untrusted lifecycle scripts (`Blocked N postinstall`). Read the script: run
  `bun pm untrusted`, read each listed script, show the list to the user, and stop and ask the user
  before `bun pm trust NAME`; it runs that package's lifecycle scripts at once. Adding a
  `trustedDependencies` list replaces Bun's built-in list, and `file:`, `git:`, and `link:` sources
  always need an entry.
- Print `bun --version` and `bun --revision` wherever Bun runs and match the version the user named;
  `packageManager` alone proves nothing.
- Record the linker and `configVersion`: migrating from npm or Yarn keeps the hoisted layout, and
  isolated installs still expose undeclared imports unless `hoist = false`.
- Keep registry tokens in environment variables and never move a private scope to the public
  registry to get past an auth error.
- Keep `tsc --noEmit` as its own step, since Bun runs TypeScript without checking it.
- Before moving Jest to `bun test`, check for `moduleNameMapper`, custom transforms, and `jsdom`,
  which have no direct equivalent. The test count must match the old runner, the setup file moves to
  `[test] preload`, and the coverage gate and report upload must point at the new files. Never run
  `bun test --update-snapshots` to get green.
- Check the Node APIs a runtime switch touches (`child_process`, `worker_threads`, `node:vm`, native
  addons) against Bun's compatibility page, and run their tests on both runtimes.
- `bun build` needs an explicit `--target` for its consumer, and esbuild, Rollup, or Vite plugins do
  not port; run the artifact on its consumer.
- A green install proves only the install. Run every moved command on the migrated tree before
  claiming success.

## Workflow

1. List each responsibility (install and lockfile, script runtime, test runner, bundler, CI, image)
   and mark which rows the request moves.
1. Run the current workflow once in a disposable copy and record the test count, build outputs, and
   runtime.
1. Migrate one row at a time, then run its moved commands and the comparison.
1. Report the rollback command (lockfile, `packageManager`, CI step, image, `bunfig.toml` keys
   revert together) and the remaining gaps.

Ask first when the request does not say whether the runtime moves and production runs the affected
scripts, or when the comparison shows versions the user did not approve.

## Scripts

- `python3 scripts/compare_lockfiles.py OLD NEW [--json]` diffs resolved versions between
  `package-lock.json` (v2/v3) and `bun.lock`. Exit 0 same, 1 different, 2 bad input or nested
  versions (diff the old tool's full list, such as `npm ls --all`, against `bun pm ls --all` then).
  On Windows, use `py -3` for `python3`.

## References

- Read [Package manager](references/package-manager.md) when converting a lockfile (including
  `bun.lockb` and npm v1), pinning Bun, setting up frozen installs, trusting lifecycle scripts,
  choosing a linker, or configuring private registries.
- Read [Runtime, tests, and bundling](references/runtime-test-build.md) when moving scripts or a
  server to Bun, Jest or `node:test` to `bun test`, a bundler to `bun build`, or planning rollback.
