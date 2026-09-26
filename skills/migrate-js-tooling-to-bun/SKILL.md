---
name: migrate-js-tooling-to-bun
description: >-
  Moves JavaScript or TypeScript tooling from npm, Yarn, or pnpm to Bun:
  installs, lockfile migration, lifecycle scripts, workspaces, bun test, and
  bun build. Use when asked to adopt Bun as package manager, test runner, or
  bundler. Not for tuning app performance.
---

# Migrate JS Tooling to Bun

Move only the named responsibilities to Bun. Keep the resolved dependency
graph, lifecycle build output, registry access, runtime, test coverage,
and build artifacts equal to the old ones unless the request changes them.

## Workflow

1. Fill the [responsibility inventory][inventory]: installation and
   lockfile, the runtime each script really starts, test runner,
   bundler, CI setup, and image. Mark which rows the request moves.
1. Pin the Bun version the user named and print `bun --version` and
   `bun --revision` wherever it runs ([version selection][version]).
1. Run the current workflow once in a disposable copy and record the
   test count, build outputs, and the runtime shown at startup.
1. Package manager: run `bun install` with the old lockfile present so
   [migration][migration] converts it. Then run
   `scripts/compare_lockfiles.py` ([comparison][compare]) and explain
   every changed line before you delete the old lockfile.
1. Review blocked lifecycle scripts with `bun pm untrusted`. Trust only
   packages whose script you read ([trust][trust]). Record the linker
   and `configVersion` ([linker][linker]).
1. Runtime, tests, or bundler: apply only the requested cards in
   [runtime, tests, and bundling](references/runtime-test-build.md).
1. Replace CI installs with `bun ci`. Also add the
   [workspace edge check][ws-gap] for workspaces. Update each CI setup
   step, image, and document that names the old tool, and leave the
   rest unchanged.
1. Run every moved command on the migrated tree. Report the results,
   the rollback unit, and the remaining compatibility gaps.

## Route the evidence to a card

| Evidence or request | Card |
| --- | --- |
| "Switch to Bun", unclear scope | [Responsibility inventory][inventory] |
| Pinning or upgrading Bun only | [Version selection][version] |
| `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` present | [Automatic migration][migration] |
| Need to prove versions did not move | [Resolution comparison][compare] |
| `bun.lockb` in the repository | [Binary lockfile conversion][lockb] |
| CI install should fail on drift | [Frozen installs][frozen] |
| Workspace repository, new internal dependency | [Workspace edge gap][ws-gap] |
| `Blocked N postinstall`, missing native binary | [trustedDependencies][trust] |
| Import works locally, fails when published | [Linker][linker] |
| Private registry, scoped packages, tokens | [Registries][registries] |
| Scripts must run on Bun, or must stay on Node | [bun run and --bun][run] |
| "Run the server on Bun" | [Direct entry][entry], [Node boundary][compat] |
| Jest or `node:test` suite to `bun test` | [Test runner][tests], [setup and coverage][coverage] |
| esbuild, Rollup, or webpack to `bun build` | [Bundler target][bundler] |
| Undo plan | [Rollback unit][rollback] |

## Rules

- Moving the package manager does not move the runtime. `bun run`
  keeps a script's `node` command on Node. Add `--bun` only when the
  request moves the runtime.
- Never run `bun update` or delete the old lockfile to get past an
  install error. Only a comparison with an explained result lets a
  version change in.
- CI installs use `bun ci`, which is the same as
  `bun install --frozen-lockfile`. In workspaces, also run
  `bun install --lockfile-only` followed by `git diff --exit-code
  bun.lock`, because frozen installs miss new `workspace:*` edges.
- Put a package in `trustedDependencies` only after reading its install
  script. A list replaces Bun's built-in trusted list. `file:`, `git:`,
  and `link:` sources always need an explicit entry.
- Keep registry tokens in environment variables. Never switch a private
  scope to the public registry.
- Keep type checking (`tsc --noEmit`) as its own step. Bun runs
  TypeScript without checking types.
- Do not run `bun test --update-snapshots` to make a suite pass. Review
  each snapshot change.
- A green install proves only that the install worked. Show a real run of
  every moved command before claiming the migration works.

## Bundled tools

- `scripts/compare_lockfiles.py OLD NEW [--json]` diffs the resolved
  versions between `package-lock.json` (v2/v3) and `bun.lock`. It exits
  0 when they are the same, 1 on a difference, and 2 on bad input or a
  graph with nested versions (then diff `bun pm ls --all` instead).
  `scripts/test_compare_lockfiles.py` holds its tests.
- `assets/examples/npm-project/` is the npm workspace before the
  migration, with `package-lock.json`. `assets/examples/fixture/` is
  the same workspace written for Bun (`workspace:*`).
- `sh assets/examples/verify.sh` exercises every card offline in a
  temporary copy. `BUN`, `NODE`, and `PYTHON` override the executables.

## References

- [Package manager](references/package-manager.md): inventory, version,
  lockfile migration and comparison, `bun.lockb`, frozen installs, the
  workspace gap, lifecycle trust, linker, and registries.
- [Runtime, tests, and bundling](references/runtime-test-build.md):
  `bun run` versus `--bun`, direct entry, the Node compatibility
  boundary, `bun test`, preload, coverage and JUnit output, the
  `bun build` target, and rollback.

## Completion evidence

- A responsibility table that lists each row as moved or kept, with the
  command that proves it.
- The Bun version and revision from every environment that runs it.
- `compare_lockfiles.py` output or the `bun pm ls --all` diff, with
  every change explained.
- The `bun pm untrusted` result and the trusted packages, with a reason
  for each.
- Test counts before and after, build artifacts checked on their
  consumer, and the runtime observed at startup.
- The CI diff, the rollback command, and known gaps, each marked
  Executed, Compiled, or Not runnable here.

## Stop and ask

- The request does not say whether the runtime moves, and production
  runs the affected scripts.
- The comparison shows changed versions that the user did not approve.
- A registry needs credentials that are not available.
- A required API, Jest feature, or bundler plugin is unsupported in the
  selected Bun version.

[inventory]: references/package-manager.md#responsibility-inventory
[version]: references/package-manager.md#bun-version-selection
[migration]: references/package-manager.md#automatic-lockfile-migration
[compare]: references/package-manager.md#resolution-comparison
[lockb]: references/package-manager.md#binary-lockfile-conversion
[frozen]: references/package-manager.md#frozen-installs-in-ci
[ws-gap]: references/package-manager.md#workspace-edge-gap
[trust]: references/package-manager.md#lifecycle-script-trust
[linker]: references/package-manager.md#linker-hoisted-or-isolated
[registries]: references/package-manager.md#registries-scopes-and-credentials
[run]: references/runtime-test-build.md#script-runtime-bun-run-and---bun
[entry]: references/runtime-test-build.md#direct-entry-point-on-bun
[compat]: references/runtime-test-build.md#node-compatibility-boundary
[tests]: references/runtime-test-build.md#test-runner-switch
[coverage]: references/runtime-test-build.md#test-setup-coverage-and-reports
[bundler]: references/runtime-test-build.md#bundler-target
[rollback]: references/runtime-test-build.md#rollback-unit
