# Running TypeScript without tsc emit

Node and Bun execute `.ts` files directly. Neither type-checks, and each
supports a different subset of TypeScript syntax. These cards say when
direct execution removes a build step and what must still go through
`tsc`. The oracle lives in `emit-cases.ts` (`imports()` and `runtimes()`);
run `sh assets/examples/verify.sh emit`.

Local environment: Node 26.8.2, Bun 1.4.2, tsc 7.0.2, Apple M1 Max, macOS.

Tier: Executed (`verify.sh emit`) for every card, except Bun's legacy
decorator path, which is cited from the Bun release notes and not run.

## Contents

- Node type stripping
- erasableSyntaxOnly as the stripping gate
- Type stripping does not type-check
- Bun native TypeScript
- Bun bundling for cross-file const enums

## Node type stripping

**Definition.** Node replaces erasable TypeScript syntax with whitespace
and runs the result; it reads no `tsconfig.json`, emits no source maps
(line numbers are preserved), and refuses `.ts` files under
`node_modules`. Enabled by default since v23.6.0 and v22.18.0, stable
since v25.2.0 and v24.12.0; `--experimental-transform-types` was removed
in v26.0.0 ([Node TypeScript][node-ts]).

**Use when.**

- Scripts, tools, tests, or servers run on Node 22.18+ and the code uses
  only erasable syntax.
- A separate `tsc --noEmit` step already type-checks in CI.

**Do not use when.**

- The code uses enums, namespaces with values, parameter properties,
  `import =` aliases, or decorators: Node fails with
  `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` (or a parser error for decorators).
- The code depends on `paths` aliases or on lowering newer syntax for an
  older target: Node ignores `tsconfig.json`.
- The package is consumed from `node_modules`: publish JavaScript.
- Types are imported without `type`: see
  [Top-level import type](emit.md#top-level-import-type); Node treats them
  as value imports and throws `SyntaxError`.

**Example.** The tsconfig that Node recommends for type-checking code it
will strip ([Node TypeScript][node-ts]):

```json
{
  "compilerOptions": {
    "noEmit": true,
    "target": "esnext",
    "module": "nodenext",
    "rewriteRelativeImportExtensions": true,
    "erasableSyntaxOnly": true,
    "verbatimModuleSyntax": true
  }
}
```

```sh
node emit/class/fields.ts        # runs directly
node --no-strip-types app.ts     # disables stripping (unknown extension)
```

Runnable: `call.ts` runs every candidate `.ts` directly in the oracle.

**Cost removed.** The `tsc` emit step and its output directory for code
run on Node. Startup did not change measurably: `node call.ts` on
`fields.ts` vs the emitted `fields.js` took 46-66 ms vs 45-80 ms (median
of 11 spawns, three shared-machine runs). Stripping removes a build step;
it is not a startup optimization.

**Verify.**

1. Behavior: the oracle compares directly executed candidates (`fields.ts`,
   `as-const.ts`, `type-only.ts`, `spread.ts`) with tsc-emitted JavaScript.
1. Benefit: no emit step is needed for those files; `verify.sh measure`
   prints `TIME node startup` so you can confirm startup did not regress.

## erasableSyntaxOnly as the stripping gate

**Definition.** `--erasableSyntaxOnly` (TypeScript 5.8+) reports `TS1294`
for enums, namespaces with runtime code, parameter properties, and
`import =`/`export =` ([TypeScript 5.8][ts58]), matching what Node's type
stripping rejects.

**Use when.**

- Any `.ts` file in the project runs under Node type stripping or another
  strip-only tool (the release notes name ts-blank-space and Amaro).

**Do not use when.**

- Only `tsc` or a full-syntax transpiler (Bun, esbuild) compiles the
  code: the flag forbids constructs that work there.

**Example.**

```sh
tsc --noEmit --erasableSyntaxOnly emit/enum/regular.ts
# emit/enum/regular.ts(2,6): error TS1294: This syntax is not allowed
# when 'erasableSyntaxOnly' is enabled.
```

**Cost removed.** Runtime `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` failures,
moved to type-check time. Count them with
`tsc --noEmit --erasableSyntaxOnly | grep -c TS1294`; the target is 0.

**Verify.**

1. Behavior: after fixing every `TS1294`, run the test suite under Node
   directly (`node --test`).
1. Benefit: the oracle asserts `TS1294` on each non-erasable baseline
   (`regular.ts`, `param-props.ts`, `ns.ts`) and none on the candidates.

## Type stripping does not type-check

**Definition.** Node "replace[s] TypeScript syntax with whitespace, and no
type checking is performed" ([Node TypeScript][node-ts]); Bun's bundler
"is not intended to replace `tsc` for typechecking"
([Bun bundler][bun-bundler]). A file with a type error runs.

**Use when.**

- Designing CI: whenever runtime execution skips emit, keep
  `tsc --noEmit` (or `tsc -b`) as a separate gate.

**Do not use when.**

- Never skip the type-check gate because tests passed under direct
  execution.

**Example.**

```typescript
export function run(): number {
  const count: number = "7";
  return Number(count) + 1;
}
```

Runnable: `runtime/type-error.ts`. `tsc` reports `TS2322`; `node` and
`bun` both return `8`.

**Cost removed.** Missed type errors in pipelines that only execute code.
Count: `tsc --noEmit | grep -c "error TS"` must be 0 in CI.

**Verify.**

1. Behavior: the oracle asserts `TS2322` from tsc.
1. Benefit (negative control): the oracle asserts Node and Bun both run
   the file and return `8`.

## Bun native TypeScript

**Definition.** Bun transpiles `.ts` files on load, including enums,
namespaces, parameter properties, and both decorator dialects (TC39
standard, and legacy when `experimentalDecorators` is set; see the
[Bun 1.3.11 notes][bun-1311] for the tsconfig fix), and does not
down-convert syntax ([Bun bundler][bun-bundler]).

**Use when.**

- The runtime is Bun and the code uses non-erasable TypeScript.
- The project wants `bun test` or `bun run` without a `tsc` emit step.

**Do not use when.**

- The same `.ts` files must also run on Node without a build: write for
  the erasable subset instead.
- You need older-target output: Bun emits modern syntax as-is.

**Example.**

```sh
bun emit/enum/regular.ts          # enum: runs
bun emit/decorators/standard.ts   # standard decorator: runs
```

**Cost removed.** The emit step for Bun-run code. Runtime cost did not
differ measurably between Bun running `.ts` and running tsc output.

**Verify.**

1. Behavior: the oracle compares `bun call.ts emit/enum/regular.ts 3000`
   with Node running the tsc output, and runs the decorator source under
   Bun.
1. Benefit: the Bun cases pass without any `tsc` output for those files.

## Bun bundling for cross-file const enums

**Definition.** `bun build` with bundling sees every module and inlines
imported `const enum` members; `bun build --no-bundle` transpiles one file
and keeps `Level.High` as a property read ([Bun bundler][bun-bundler];
observed locally).

**Use when.**

- Const enums cross module boundaries and the build uses Bun.

**Do not use when.**

- Output is produced per file (`--no-bundle`, library builds that keep
  modules): the enum object must exist at runtime, so declare it as a
  regular enum or an `as const` object.

**Example.**

```sh
bun build emit/enum/use-levels.ts --target node
# console output contains: return n > 10 ? 2 /* High */ : 1 /* Low */;
bun build emit/enum/use-levels.ts --no-bundle
# keeps: import { Level } from "./levels.ts"; ... Level.High
```

**Cost removed.** The enum object and property reads, in bundled output.

**Verify.**

1. Behavior: run the bundle and compare with the unbundled module.
1. Benefit: the oracle asserts the bundled output lacks `Level.High` and
   the `--no-bundle` output keeps it.

[node-ts]: https://nodejs.org/api/typescript.html
[ts58]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html
[bun-bundler]: https://bun.com/docs/bundler
[bun-1311]: https://bun.com/blog/bun-v1.3.11
