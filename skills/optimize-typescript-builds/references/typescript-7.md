# TypeScript 7 native compiler

TypeScript 7.0 (released July 8, 2026) is the Go port of the compiler,
published as the `typescript` package with its own `tsc` binary
([announcement][ts7]). It keeps TypeScript 6.0's type-checking behavior,
adopts 6.0's defaults, and turns 6.0 deprecations into hard errors. The
oracle in `checker-cases.ts` (`nativeCompiler()`) runs these checks only
when `tsc --version` reports 7 or later; older compilers print `SKIP`.

Local: `node_modules/.bin/tsc --version` prints `Version 7.0.2`; the
package resolves a platform binary (`@typescript/typescript-darwin-arm64`)
and its trace metadata names the process `tsgo`. Apple M1 Max (10 cores),
macOS, shared machine.

Tier: Executed (`verify.sh checker` and `verify.sh measure`), except
parallel builders (smoke run only, no timing) and tsc6 (not runnable here).

## Contents

- Identify the compiler and removed options
- New defaults from TypeScript 6.0
- Parallel type checkers
- Parallel project builders
- Single-threaded mode for comparable counters
- Side-by-side tsc6 for API consumers

## Identify the compiler and removed options

**Definition.** tsc 7 rejects options deprecated in 6.0 with errors such
as `TS5108: Option 'target=ES5' has been removed` and `TS5102: Option
'downlevelIteration' has been removed`. The removed set includes
`target: es5`, `downlevelIteration`, `moduleResolution` `node`/`node10`
and `classic`, `module` `amd`/`umd`/`systemjs`/`none`, `baseUrl`,
`esModuleInterop: false`, `allowSyntheticDefaultImports: false`, and
`alwaysStrict: false` ([announcement][ts7]).

**Use when.**

- Starting any compiler-performance or emit task: record
  `tsc --version` and `tsc --showConfig` before trusting flags from older
  documentation.

**Do not use when.**

- Never assume a 5.x flag exists on 7: `--generateCpuProfile` is still
  listed by `tsc --help --all` but wrote no file locally; use `--pprofDir`
  (see [measurement](measurement.md#go-pprof-profiles)).

**Example.**

```sh
tsc --version                    # Version 7.0.2
tsc --showConfig -p tsconfig.json
tsc app.ts --noEmit --target es5
# error TS5108: Option 'target=ES5' has been removed. Please remove it
# from your configuration.
```

**Cost removed.** Failed CI runs after an upgrade, and advice written for
the wrong compiler. Count removed options with
`tsc -p . --noEmit | grep -cE "TS510[28]"`; the target is 0.

**Verify.**

1. Behavior: after removing each flagged option, `tsc -p . --noEmit`
   reports the same diagnostics as before the upgrade (with 6.0).
1. Benefit: the oracle asserts `TS5108`/`TS5102` for `--target es5`,
   `--downlevelIteration`, `--baseUrl`, and `--moduleResolution node10`.

## New defaults from TypeScript 6.0

**Definition.** With no explicit setting, tsc 7 uses `strict: true`,
`module: esnext`, `target` equal to the latest stable ECMAScript version
before `esnext` (`es2025` in `tsc --help --all`), `types: []`,
`rootDir: "./"`, `noUncheckedSideEffectImports: true`, and
`libReplacement: false`; `stableTypeOrdering` is always on
([announcement][ts7]).

**Use when.**

- A project upgraded from 5.x shows new "Cannot find name 'process'"
  errors (`types` is now `[]`), or `TS5011: The common source directory
  of 'tsconfig.json' is './src'. The 'rootDir' setting must be explicitly
  set` (observed locally when `include` is `["src"]` and `rootDir` is
  unset; tsc still emitted to `dist/src/`).

**Do not use when.**

- Measuring a performance change across the upgrade with these options
  unpinned: a different `types` or `target` changes both the checked
  program and the emitted code.

**Example.**

```json
{
  "compilerOptions": {
    "rootDir": "./src",
    "outDir": "dist",
    "types": ["node"],
    "target": "es2022"
  },
  "include": ["./src"]
}
```

**Cost removed.** Unplanned output-layout and global-type changes. The
explicit `types` list is also the [scoped types
array](build.md#scoped-types-array) card.

**Verify.**

1. Behavior: `tsc --showConfig` prints the same effective options before
   and after the upgrade; the oracle asserts that an explicit `rootDir`
   emits `dist2/a.js` with exit status 0.
1. Benefit: the oracle asserts a config without `types` loads the same
   `Files` and `Symbols` as `"types": []`, and that the unset-`rootDir`
   project reports `TS5011`.

## Parallel type checkers

**Definition.** tsc 7 splits files across a fixed number of type-checker
workers, default 4, set with `--checkers N`; each worker duplicates some
shared work, so memory grows with N, and "in rare cases, varying the
number of `--checkers` may surface order-dependent results"
([announcement][ts7]).

**Use when.**

- `Check time` dominates `--extendedDiagnostics` and the machine has spare
  cores and memory.
- CI runners are small: lower N to cut memory.

**Do not use when.**

- Comparing `Types`, `Instantiations`, or `Memory used` between two code
  versions: they change with N (locally `Types` 8,875 with 1 checker vs
  9,508 with 4). Use `--singleThreaded` for those comparisons.
- Different machines must produce identical diagnostics: pin N
  explicitly.

**Example.**

```sh
tsc -p . --noEmit --extendedDiagnostics --checkers 8
```

**Cost removed.** Wall time of the check phase. Published: vscode builds
in 10.6 s with the default 4 checkers and 7.51 s with 8, against 125.7 s
on TypeScript 6 ([announcement][ts7]). Local (8 generated files):
`Check time` median 0.50-0.64 s (1), 0.26-0.50 s (2), 0.12-0.19 s (4),
0.09-0.19 s (8); `Memory used` 77,576K (1) to 78,327K (4).

**Verify.**

1. Behavior: the oracle asserts identical diagnostics with `--checkers 1`
   and `--checkers 4`.
1. Benefit: `verify.sh measure` prints `TIME check --checkers N` for 1, 2,
   4, and 8.

## Parallel project builders

**Definition.** `--builders N` sets how many referenced projects
`tsc -b` builds at once; it multiplies with `--checkers` (4 builders with
4 checkers allow 16 checkers), and unlike checkers it "should not produce
different results" ([announcement][ts7]).

**Use when.**

- `tsc -b --verbose` shows independent projects built one after another
  and memory allows more concurrency.

**Do not use when.**

- The reference graph is a chain: each dependent waits for its
  references, so builders cannot overlap.
- Memory is the constraint: reduce `--checkers` when raising builders.

**Example.**

```sh
tsc -b tsconfig.json --builders 4 --checkers 2 --verbose
```

**Cost removed.** Idle cores during multi-project builds. Not measured
locally beyond a smoke run: the two-project fixture is a chain.

**Verify.**

1. Behavior: the oracle runs `tsc -b gen/refs/app --force --builders 2`
   and requires exit status 0.
1. Benefit: time `tsc -b --force` with `--builders 1` and a higher value
   on your own graph (for example with `hyperfine`); report both.

## Single-threaded mode for comparable counters

**Definition.** `--singleThreaded` disables all parallelism in tsc 7
([announcement][ts7]); counters from `--extendedDiagnostics` then depend
only on the program, not on how files were split across workers.

**Use when.**

- Comparing baseline and candidate `Types`, `Instantiations`, `Symbols`,
  or `Memory used` for a type-level change.
- Producing a trace whose hot spots are not interleaved across workers.

**Do not use when.**

- Reporting real build time: users run the parallel default.

**Example.**

```sh
tsc -p . --noEmit --singleThreaded --extendedDiagnostics
```

**Cost removed.** False positives and negatives in counter comparisons.
Locally, the same 8-file program reported `Types` 8,875 single-threaded and
9,508 with 4 checkers; single-threaded counters repeated exactly across
runs.

**Verify.**

1. Behavior: run the command twice; the counters must be identical.
1. Benefit: every checker oracle in `verify.sh checker` uses this flag and
   compares exact counters.

## Side-by-side tsc6 for API consumers

**Definition.** TypeScript 7.0 ships no stable programmatic API (planned
for 7.1); the `@typescript/typescript6` package provides a `tsc6` binary
and re-exports the 6.0 API for tools such as typescript-eslint
([announcement][ts7]).

**Use when.**

- A lint, codegen, or framework tool imports `typescript` as a library and
  breaks after upgrading to 7.
- The project uses Vue, MDX, Astro, or Svelte: the announcement says
  those workflows "will need to continue using TypeScript 6.0 for now".

**Do not use when.**

- Only the `tsc` command line is used: stay on 7.

**Example.** Install with Bun, aliasing the package as the announcement
describes:

```sh
bun add -d typescript@npm:@typescript/typescript6@^6.0.2
```

That leaves only a `tsc6` executable; keep 7 for command-line checks under
another alias if both are needed.

**Cost removed.** A forced downgrade of the whole toolchain.

**Verify.** Not runnable here: the package is not installed locally and
installing it requires the network.

1. Behavior: after installing, run the dependent tool's own command (for
   example the lint job) and compare its output with the pre-upgrade run.
1. Benefit: `bunx tsc6 --version` reports 6.x while the command-line
   `tsc` used for builds still reports 7.

[ts7]: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
