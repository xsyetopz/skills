---
name: optimize-typescript-builds
description: >-
  Speeds up TypeScript type checking, tsc and tsgo builds, project
  references, and editor responsiveness. Use when tsc is slow or runs out of
  memory. Not for runtime JavaScript speed.
---

# Optimize TypeScript Builds

Make TypeScript cheaper to type-check and build without changing emitted output or the declared
types. Runtime speed of the emitted JavaScript belongs to the optimize-code-performance skill.

## Rules

- Attribute the cost before changing config:
  `tsc -p . --noEmit --singleThreaded --extendedDiagnostics`, then `--generateTrace DIR` with
  `@typescript/analyze-trace`. Changing flags by habit fixes the wrong phase; only a dominant
  `Check time` points at types, and `Parse time` points at program size (`--listFilesOnly`,
  `--explainFiles`).
- Compare counters only with `--singleThreaded` (or the same `--checkers N`) and the same tsc
  version, and delete the `*.tsbuildinfo` files (see `tsBuildInfoFile` and `outDir`) first. tsc 7
  changes `Types` and `Memory used` with the worker count, and a warm `.tsbuildinfo` hides the real
  check.
- Check `tsc --version` and `tsc --showConfig` before using flags. tsc 7 (the Go port) removes
  `target: es5`, `downlevelIteration`, `baseUrl`, and `moduleResolution: node10` (`TS5108`,
  `TS5102`) and defaults `types` to `[]`; advice from 5.x docs breaks there. See [TypeScript
  7](references/typescript-7.md).
- Do not add `skipLibCheck` by reflex. It also skips your own hand-written `.d.ts` files and can
  hide conflicts, so measure with and without it, diff the errors once, and keep one CI check
  without it when the repo has hand-written `.d.ts` files (`git ls-files '*.d.ts'` outside build
  output). Use it in both runs when measuring a type-level change.
- `isolatedDeclarations` alone does not speed up tsc. It needs an explicit annotation on every
  export (`TS90xx` otherwise), and the gain comes from emitting declarations without type-checking
  (`--noCheck` or another emitter) next to a separate `tsc --noEmit` that still reports errors.
- Do not weaken public types (`any`, `object`, a base interface) to save checking time without the
  API owner. Prove an edit changed nothing with the project's type tests or a mutual-assignability
  probe (`Eq<Before, After>`).
- Split repeated full re-checks with `composite` project references and `tsc -b`, or `incremental`
  with a persisted `.tsbuildinfo`. A `.tsbuildinfo` not restored between CI runs only adds a write.
  References must form a DAG; split along the existing package graph (typically 5 to 20 projects).
- Edit a type only when a trace names it: large unions in hot signatures, `A & B & C` compared
  often, conditional return types, `TS2589` recursion. Some wiki advice has no measured gain on tsc
  7 (named conditional types); keep an edit only if the counter that justified it dropped. See
  [Build settings and type costs](references/build-and-types.md).
- Narrow `include` and `types` only after `--listFilesOnly` shows surplus files, and keep tests
  type-checked in their own project. A `types` list that omits `node` or a test framework fails with
  "Cannot find name".
- Node and Bun strip types without checking. Keep `tsc --noEmit` or `tsc -b` in CI wherever code
  runs without a tsc emit.
- Timing claims need at least 5 runs on a quiet machine; report the median and spread. Report a
  change with no measured gain as null instead of keeping it.

## Workflow

1. Record `tsc --version`, the effective options, and the baseline counters with the command above.
1. Attribute with the trace or the file list, apply one change, and rerun the same command with the
   same flags.
1. Run the normal build and tests, and keep the change only if the counter or time dropped and
   diagnostics are unchanged.

## References

- Read [Measurement](references/measurement.md) when attributing cost: counters, traces, tsc 7
  profiles, and program-size checks.
- Read [Build settings and type costs](references/build-and-types.md) when choosing `skipLibCheck`,
  incremental builds, project references, `isolatedDeclarations`, `--noCheck`, or editing expensive
  types.
- Read [TypeScript 7](references/typescript-7.md) when the compiler is tsc 7 or tsgo, for removed
  options, new defaults, `--checkers`, `--builders`, and `tsc6`.
