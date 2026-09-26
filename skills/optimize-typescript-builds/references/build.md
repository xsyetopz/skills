# Build configuration constructs

Each card changes what `tsc` loads, checks, or re-checks. The oracle in
`checker-cases.ts` generates each project in the disposable work copy and
asserts a deterministic counter from `--extendedDiagnostics` or
`--listFilesOnly`. Run `sh assets/examples/verify.sh checker`.

Local numbers: tsc 7.0.2, `--singleThreaded`, Apple M1 Max, macOS. Timings
come from a shared machine and are reported, not asserted.

Tier: Executed (`verify.sh checker`).

## Contents

- skipLibCheck
- Scoped types array
- Scoped include
- Incremental builds with tsBuildInfo
- Project references with tsc -b
- Isolated declarations with noCheck
- Emit without checking

## skipLibCheck

**Definition.** `skipLibCheck` skips type-checking every `.d.ts` file
(including the default `lib` files and `node_modules` types); declarations
are still loaded and used to check your sources ([tsconfig
skipLibCheck][tsc-skiplib], [Performance wiki][wiki], "Skipping .d.ts
Checking").

**Use when.**

- `--extendedDiagnostics` shows `Check time` or `Types` dominated by
  declaration files (compare a run with and without the flag).
- The authors of the dependencies already type-check their `.d.ts` files.

**Do not use when.**

- The project has hand-written `.d.ts` files that nothing else checks:
  the wiki warns the flags "can often hide misconfiguration and
  conflicts". If that risk matters, keep a separate job without the flag.

**Example.**

```json
{ "compilerOptions": { "skipLibCheck": true } }
```

**Cost removed.** Checking `lib.*.d.ts` and dependency declarations.
Local (a one-line source file with the default `lib`): `Types` 30,927 to
94, `Instantiations` 32,820 to 1, `Memory used` 61,383K to 24,710K,
`Check time` 0.25-0.39 s to 0 s.

**Verify.**

1. Behavior: both runs report zero errors in your sources. Diff the error
   list with and without the flag once to see what it hides.
1. Benefit: `METRIC skip-lib-check Types: 30927 -> 94`.

## Scoped types array

**Definition.** `compilerOptions.types` lists which `@types` packages are
loaded globally. TypeScript 6.0 changed the default to `[]`, which tsc 7
adopts; `["*"]` restores automatic inclusion of every visible `@types`
package ([TypeScript 7 announcement][ts7], [tsconfig types][tsc-types],
[Performance wiki][wiki], "Controlling @types Inclusion").

**Use when.**

- `--explainFiles` shows `@types` packages included only automatically
  ("Entry point for implicit type library").
- A project on TypeScript 5.x (default: all visible `@types`) is slow in
  program construction.

**Do not use when.**

- The code uses globals from a package (`process` from `@types/node`,
  `describe` from test frameworks) and the list would omit it: list those
  packages explicitly, such as `"types": ["node"]`, or builds fail with
  "Cannot find name" errors.

**Example.**

```json
{ "compilerOptions": { "types": ["node"] } }
```

**Cost removed.** Parsing and binding unused global declarations. Local
(a generated `@types/big` with 3,000 declarations): `Files` 84 to 83,
`Symbols` 44,126 to 32,126, `Memory used` 31,412K to 24,777K.

**Verify.**

1. Behavior: the project still type-checks with zero errors.
1. Benefit: `METRIC types-array Files: 84 -> 83` and
   `METRIC types-array Symbols: 44126 -> 32126`.

## Scoped include

**Definition.** `include` globs decide which files enter the program; a
broad pattern (the default `**/*`, or `"."`) also pulls in fixtures,
generated code, and build output ([Performance wiki][wiki], "Specifying
Files" and "Misconfigured include and exclude").

**Use when.**

- `tsc --listFilesOnly` lists files outside the source roots.

**Do not use when.**

- The narrower include would drop test files that must be type-checked:
  give them their own project (see
  [project references](#project-references-with-tsc--b)).

**Example.**

```json
{
  "compilerOptions": { "noEmit": true },
  "include": ["src"],
  "exclude": ["**/node_modules", "**/.*/"]
}
```

**Cost removed.** Parsing, binding, and checking files that are not part
of the build. Local (50 generated fixture files next to `src`): listed
files 133 to 83.

**Verify.**

1. Behavior: `tsc -p tsconfig.json --noEmit` still reports zero errors and
   every entry point is listed by `--listFilesOnly`.
1. Benefit: `METRIC include listed files: 133 -> 83`; for real projects
   compare `tsc --listFilesOnly | wc -l` before and after.

## Incremental builds with tsBuildInfo

**Definition.** `incremental` saves program state to a `.tsbuildinfo` file
(`tsBuildInfoFile` sets its path); later runs re-check only files whose
inputs changed ([tsconfig incremental][tsc-incremental], [Performance
wiki][wiki], "Incremental Project Emit").

**Use when.**

- The same project is type-checked repeatedly (local runs, CI with a cache
  restored between jobs).

**Do not use when.**

- The `.tsbuildinfo` file is not persisted between runs: every run is cold
  and pays the extra write.
- Measuring type-check cost: delete the `.tsbuildinfo` first, or you
  measure a warm cache.

**Example.**

```json
{
  "compilerOptions": {
    "incremental": true,
    "noEmit": true,
    "tsBuildInfoFile": "cache/app.tsbuildinfo"
  }
}
```

**Cost removed.** Re-checking unchanged files. Local (the union fixture):
cold `Check time` 0.97-1.49 s, warm `Check time` 0 s and `Types` 85;
after a comment was appended to the only file, `Check time` returned to
about 0.4 s.

**Verify.**

1. Behavior: after a real edit, the warm run reports the same errors as a
   cold run (`rm cache/app.tsbuildinfo` and compare).
1. Benefit: `METRIC incremental Check time s` drops to 0 on the unchanged
   second run and `gen/incr/cache/app.tsbuildinfo` exists.

## Project references with tsc -b

**Definition.** A project with `composite: true` can be referenced from
another project's `references`; `tsc -b` builds referenced projects in
dependency order, skips up-to-date ones, and dependents read their `.d.ts`
outputs instead of re-checking sources ([Project references][refs]).

**Use when.**

- A repository has separable parts (libraries, app, tests) and edits
  usually touch one part.
- The wiki's guidance fits: roughly 5 to 20 projects that mirror the
  dependency graph ([Performance wiki][wiki], "Using Project References").

**Do not use when.**

- Parts have circular imports: references must form a DAG.
- Consumers must see source changes without rebuilding the referenced
  project.

**Example.**

```json
{
  "compilerOptions": { "composite": true, "outDir": "dist", "rootDir": "." },
  "include": ["main.ts"],
  "references": [{ "path": "../core" }]
}
```

```sh
tsc -b gen/refs/app --verbose     # builds core, then app
tsc -b gen/refs/app --verbose     # "... is up to date" for both
```

**Cost removed.** Checking and emitting unchanged projects. Locally, the
second `tsc -b --verbose` reports both projects up to date. Since
TypeScript 5.6, `--build` continues past errors in dependencies unless
`--stopOnBuildErrors` is set ([TypeScript 5.6][ts56]).

**Verify.**

1. Behavior: `tsc -b` exits 0 and `core/dist/index.d.ts` exists.
1. Benefit: the oracle counts at least 2 "up to date" lines on the second
   run.

## Isolated declarations with noCheck

**Definition.** `isolatedDeclarations` (TypeScript 5.5+, requires
`declaration` or `composite`) requires every export to be annotated enough
to emit `.d.ts` without type inference; with `--noCheck`
(TypeScript 5.6+) tsc then emits declarations "without a type-checking
pass" ([TypeScript 5.5][ts55], [TypeScript 5.6][ts56]).

**Use when.**

- Declaration emit blocks downstream projects in a references graph, or
  a faster tool should generate `.d.ts` in parallel.

**Do not use when.**

- Exported functions rely on inferred return types and cannot be
  annotated: every such export fails with a `TS90xx` error. The 5.5 notes
  say enabling the flag in tsc alone "won't immediately bring about the
  potential benefits".

**Example.**

```sh
tsc gen/ret/annotated.ts --declaration --emitDeclarationOnly \
  --skipLibCheck --isolatedDeclarations --noCheck --outDir out/decl-fast
```

**Cost removed.** The type-checking pass during declaration emit. Local
(200 annotated exports): `Types` 1,099 to 285 with identical `.d.ts`
output. An unannotated `export function make(n: number) { return
compute(n); }` fails with `TS9013` locally.

**Verify.**

1. Behavior: the oracle asserts the `.d.ts` from the checked and the
   `--noCheck` builds are byte-identical. Run `tsc --noEmit` separately so
   errors are still reported.
1. Benefit: `METRIC isolated-declarations Types: 1099 -> 285`.

## Emit without checking

**Definition.** `--noCheck` (TypeScript 5.6+) skips type-checking of all
inputs and emits JavaScript; only critical parse and emit errors are
reported ([TypeScript 5.6][ts56]).

**Use when.**

- A pipeline needs the JavaScript quickly and a separate `tsc --noEmit`
  job (or watch) reports type errors.

**Do not use when.**

- The emit job is the only place type errors would be seen.
- Emit depends on type information (`emitDecoratorMetadata`, `const enum`
  inlining across files): confirm the output matches a checked build
  before switching.

**Example.**

```sh
tsc -p tsconfig.json --noCheck        # emit only
tsc -p tsconfig.json --noEmit         # type errors, in parallel
```

**Cost removed.** The check phase during emit. Local (union fixture):
`Types` 3,094 to 85, `Check time` 1.20 s to 0 s, byte-identical `.js`.

**Verify.**

1. Behavior: the oracle asserts identical emitted JavaScript with and
   without `--noCheck`.
1. Benefit: `METRIC no-check-emit Types: 3094 -> 85`.

[tsc-skiplib]: https://www.typescriptlang.org/tsconfig/#skipLibCheck
[wiki]: https://github.com/microsoft/TypeScript/wiki/Performance
[ts7]: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
[tsc-types]: https://www.typescriptlang.org/tsconfig/#types
[tsc-incremental]: https://www.typescriptlang.org/tsconfig/#incremental
[refs]: https://www.typescriptlang.org/docs/handbook/project-references.html
[ts56]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-6.html
[ts55]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html
