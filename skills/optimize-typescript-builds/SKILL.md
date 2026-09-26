---
name: optimize-typescript-builds
description: >-
  Speeds up TypeScript type-checking, builds, and emit: tsc diagnostics and
  traces, incremental builds, project references, skipLibCheck, emit targets,
  type stripping. Use when tsc or a TypeScript build is slow. Not for
  JavaScript runtime speed.
---

# Optimize TypeScript Builds

Make TypeScript cheaper to type-check, build, or run without changing
emitted behavior or the declared types. TypeScript cost has two separate
sources: the compiler's work (checker, program size, declaration emit) and
the JavaScript that TypeScript constructs and `target` produce. Each change
applies one reference card to a cost that a counter, trace, emitted-code
diff, or runtime profile attributes, is proven equivalent by an oracle, and
is kept only if the metric the card names improves. Engine-level JavaScript
tuning (object shapes, array kinds) belongs to the optimize-javascript-code
skill.

## Workflow

1. Identify the compiler and effective options: `tsc --version` and
   `tsc --showConfig -p tsconfig.json`. tsc 7 is the Go port with removed
   options and new defaults; read
   [TypeScript 7](references/typescript-7.md) before using flags from
   older docs. Record Node/Bun versions and any other transpiler (Bun,
   esbuild, SWC) that produces the shipped JavaScript.
1. Classify the claim: compile time, declaration output, emitted-code
   size, or runtime. Measure each claim with its own tool; a faster type
   check is not a runtime improvement, and type-only edits change no
   runtime cost.
1. Attribute before editing:
   - compile time: `tsc -p . --noEmit --singleThreaded
     --extendedDiagnostics`, then `--generateTrace` and analyze-trace
     ([measurement](references/measurement.md));
   - program size: `tsc --listFilesOnly` and `--explainFiles`;
   - runtime: compile baseline to a directory, diff emitted JavaScript,
     then profile the running program with the runtime's profiler.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first. Runtime: same inputs through baseline and
   candidate output, including error paths. Types: the project's type
   tests plus a mutual-assignability probe for changed exports
   (`Eq<A, B>` in [checker][return-types]).
1. Apply the change and run the card's **Verify** steps: behavior first,
   then the metric, with the same options and the same tsc version.
1. Re-run the project build and tests end to end. Keep the change only if
   the metric moved and nothing regressed; report null results.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| Enum IIFEs in output, enum property loads | [Const enum](references/emit.md#const-enum), [As const object](references/emit.md#as-const-object-instead-of-enum) |
| Const enum not inlined under `isolatedModules` | [Const enum under isolatedModules](references/emit.md#const-enum-under-isolatedmodules) |
| `TS1294`, `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` | [erasableSyntaxOnly](references/runtimes.md#erasablesyntaxonly-as-the-stripping-gate), [Explicit fields](references/emit.md#explicit-fields-instead-of-parameter-properties), [ES module](references/emit.md#es-module-instead-of-namespace) |
| `__awaiter` / generator frames in profiles | [Native async](references/emit.md#native-async-functions-from-es2017) |
| `WeakMap`, `__classPrivateFieldGet` in output | [Native private fields](references/emit.md#native-private-fields-from-es2022) |
| `Object.assign(Object.assign({}` in output | [Native object spread](references/emit.md#native-object-spread-from-es2018) |
| Same helper copied into many files | [importHelpers](references/emit.md#importhelpers-with-tslib) |
| Field `undefined` after a target bump, `TS2612` | [Declare fields](references/emit.md#declare-for-redeclared-fields) |
| `SyntaxError` at `@decorator` on Node | [Standard decorators](references/emit.md#standard-decorators-and-the-target) |
| Modules loaded only for decorated constructor types | [Decorator metadata](references/emit.md#decorator-metadata-retains-imports) |
| Module evaluated for a type-only import | [Top-level import type](references/emit.md#top-level-import-type) |
| Remove a build step for Node or Bun | [Node stripping](references/runtimes.md#node-type-stripping), [Bun](references/runtimes.md#bun-native-typescript), [No type-check](references/runtimes.md#type-stripping-does-not-type-check) |
| Cross-file const enums with Bun | [Bun bundling](references/runtimes.md#bun-bundling-for-cross-file-const-enums) |
| High `Check time`, large unions in hot signatures | [Base type](references/checker.md#base-type-instead-of-a-large-union) |
| `A & B & C` object compositions compared often | [Interfaces](references/checker.md#interfaces-instead-of-intersections) |
| `TS2589` excessively deep instantiation | [Tail recursion](references/checker.md#tail-recursive-conditional-types) |
| Conditional return types re-evaluated | [Named conditional types](references/checker.md#named-conditional-types) |
| Large `.d.ts`, inferred export types | [Return types](references/checker.md#explicit-return-types-on-exports) |
| Checking dominated by `.d.ts` files | [skipLibCheck](references/build.md#skiplibcheck) |
| Unused `@types` packages in the program | [types array](references/build.md#scoped-types-array) |
| Fixtures or output in `--listFilesOnly` | [include](references/build.md#scoped-include) |
| Repeated full re-checks | [Incremental](references/build.md#incremental-builds-with-tsbuildinfo), [Project references](references/build.md#project-references-with-tsc--b) |
| Declaration emit blocks dependents | [isolatedDeclarations](references/build.md#isolated-declarations-with-nocheck) |
| JavaScript needed before the check finishes | [noCheck emit](references/build.md#emit-without-checking) |
| `TS5102`/`TS5108` after upgrading | [Removed options](references/typescript-7.md#identify-the-compiler-and-removed-options), [New defaults](references/typescript-7.md#new-defaults-from-typescript-60) |
| Idle cores or memory pressure during tsc 7 | [Checkers](references/typescript-7.md#parallel-type-checkers), [Builders](references/typescript-7.md#parallel-project-builders) |
| Lint/tools need the `typescript` API on 7 | [tsc6](references/typescript-7.md#side-by-side-tsc6-for-api-consumers) |

## Rules

- Compare compiler counters only with `--singleThreaded` (or the same
  `--checkers N`) and the same tsc version; tsc 7 changes `Types` and
  `Memory used` with the worker count. Delete `.tsbuildinfo` before cold
  measurements.
- Use `--skipLibCheck` in both runs when measuring a type-level change, or
  lib checking hides it; measure skipLibCheck itself separately.
- A type-only change has no runtime effect. Claim runtime changes only
  from emitted-code diffs plus a runtime measurement in the target
  runtime.
- Changing `target` changes class-field semantics at ES2022 and object
  spread semantics at ES2018 as well as speed. Run the field and spread
  oracles before a target bump.
- Node and Bun do not type-check. Keep `tsc --noEmit` (or `tsc -b`) in CI
  whenever code runs without tsc emit.
- Do not weaken public types (to `any`, `object`, a base type) to speed up
  checking unless the API owner agrees; prove equality with a probe.
- Timing claims need repeated runs on a quiet machine. Record null
  results (named conditionals, namespace-to-module speed) instead of
  hiding them.

## Bundled tools

- `assets/examples/verify.sh verify|emit|checker|benchmark|measure|trace`:
  copies the examples to a temp directory and runs the oracles with
  `node harness.ts`. `verify` (and `benchmark`, a smoke alias) checks
  every card's behavior and deterministic metric; `measure` adds
  machine-specific timings; `trace` runs analyze-trace. tsc comes from
  `TSC`, then `./node_modules/.bin/tsc`, then `PATH`. Needs Node 22.18+;
  Bun is optional (tslib install, Bun cases).
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): counters, traces, pprof, file
  inclusion, emitted-code diffs, runtime timing.
- [Emit](references/emit.md): enums, classes, namespaces, target
  lowering, helpers, decorators, imports.
- [Runtimes](references/runtimes.md): Node type stripping,
  erasableSyntaxOnly, Bun.
- [Checker](references/checker.md): unions, intersections, recursion,
  conditional types, return types.
- [Build](references/build.md): skipLibCheck, types, include, incremental,
  project references, isolated declarations, noCheck.
- [TypeScript 7](references/typescript-7.md): removed options, defaults,
  checkers, builders, single-threaded mode, tsc6.
- [Sources](references/sources.md): primary documentation per card.

## Completion evidence

The final report contains:

- tsc version, effective options that matter (`target`, `module`,
  `isolatedModules`, `verbatimModuleSyntax`, `types`, `skipLibCheck`),
  runtime versions, OS/CPU, and the transpiler that ships the code;
- the counter, trace, file listing, or emitted-code diff that attributed
  the cost;
- the card applied, with its **Use when** items checked and **Do not use
  when** items ruled out;
- the oracle command and result: type tests, assignability probes, and
  runtime equivalence including error paths;
- baseline and candidate metrics from the same command and flags
  (`--singleThreaded` counters, `.d.ts` bytes, helper counts, medians);
- anything not run (other runtimes, other tsc versions, bundler output)
  stated as not verified.

[return-types]: references/checker.md#explicit-return-types-on-exports
