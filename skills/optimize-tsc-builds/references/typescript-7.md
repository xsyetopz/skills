# TypeScript 7 Native Compiler

Source: [Announcing TypeScript 7.0][1] unless stated. TypeScript 7.0 is the Go port of the compiler,
published as the `typescript` package with its own `tsc` binary. It keeps 6.0's type-checking
behavior and defaults, and turns 6.0 deprecations into errors.

## Contents

- [Removed Options](#removed-options)
- [New Defaults](#new-defaults)
- [Parallelism Flags](#parallelism-flags)
- [tsc6 for API Consumers](#tsc6-for-api-consumers)

## Removed Options

- Run `tsc --version` and `tsc --showConfig -p tsconfig.json` before using flags from older docs.
  tsc 7 fails with `TS5108` or `TS5102` on the removed set: `target: es5`, `downlevelIteration`,
  `moduleResolution` `node`/`node10`/`classic`, `module` `amd`/`umd`/`systemjs`/`none`, `baseUrl`,
  `esModuleInterop: false`, `allowSyntheticDefaultImports: false`, and `alwaysStrict: false`.
- Remove each flagged option, then confirm `tsc --noEmit` reports the same diagnostics as 6.0.

## New Defaults

- Unset options now mean `strict: true`, `module: esnext`, `target` the latest stable ECMAScript
  before `esnext`, `types: []`, `rootDir: "./"`, `noUncheckedSideEffectImports: true`, and
  `libReplacement: false`; `stableTypeOrdering` is always on.
- Symptoms after an upgrade from 5.x: "Cannot find name 'process'" (set `"types": ["node"]`) and
  `TS5011` about the common source directory (set `rootDir`).
- Pin `types`, `target`, and `rootDir` before comparing performance across the upgrade, because they
  change both the checked program and the output.

## Parallelism Flags

- `--checkers N` (default 4) sets the type-checker workers. Memory grows with N because workers
  duplicate shared work, and the announcement notes that varying it "may surface order-dependent
  results". Raise it when `Check time` dominates and cores are free; lower N when it exceeds the
  runner's cores or the job hits its memory limit.
- `--builders N` sets how many referenced projects `tsc -b` builds at once, multiplies with
  `--checkers` (4 by 4 allows 16 checkers), and should not change results.
- `--singleThreaded` disables all parallelism. Use it for comparable counters and readable traces,
  never for reporting real build time.

## tsc6 for API Consumers

- 7.0 ships no stable programmatic API (planned for 7.1). Tools that import `typescript` as a
  library (typescript-eslint, codegen, Vue, MDX, Astro, Svelte workflows) need the side-by-side
  package: install `typescript@npm:@typescript/typescript6@^6.0.2` as a dev dependency with the
  project's package manager (`bun add -d ...` in a Bun project), which provides a `tsc6` binary and
  the 6.0 API.
- That alias leaves no `tsc` 7 binary; install 7 under another alias if command-line checks should
  stay on 7. If only the `tsc` command is used, stay on 7.

[1]: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
