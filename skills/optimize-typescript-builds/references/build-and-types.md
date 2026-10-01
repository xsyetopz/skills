# Build settings and type costs

Sources: [Performance wiki][1], [TSConfig reference][2], [Project references][3], [TypeScript
4.5][4], [TypeScript 5.5][5], [TypeScript 5.6][6].

## Contents

- [skipLibCheck](#skiplibcheck)
- [Incremental builds](#incremental-builds)
- [Project references](#project-references)
- [isolatedDeclarations and noCheck](#isolateddeclarations-and-nocheck)
- [Explicit return types on exports](#explicit-return-types-on-exports)
- [Large unions](#large-unions)
- [Intersections](#intersections)
- [Recursive conditional types](#recursive-conditional-types)
- [Named conditional types](#named-conditional-types)

## skipLibCheck

- It skips type-checking every `.d.ts` (default `lib` files, `node_modules` types, and your own
  hand-written declarations), but the declarations still type your sources. Apply it only when
  `Check time` or `Types` drops clearly with the flag.
- The wiki warns it "can often hide misconfiguration and conflicts". Diff the error list with and
  without it once, and keep a CI check without it when the repo has hand-written `.d.ts` files.
- When measuring a type-level change, use it in both runs so lib checking does not hide the effect.
  Measure the flag itself separately.

## Incremental builds

- `incremental` with `tsBuildInfoFile` re-checks only changed files. It helps only if the
  `.tsbuildinfo` persists between runs (restore it in CI cache); otherwise every run is cold and
  pays the write.
- After an edit, compare the warm errors with a cold run (delete the file and rerun).

## Project references

- `composite: true` on the referenced project, `references` on the dependent, and `tsc -b`.
  Dependents read the `.d.ts` outputs instead of re-checking sources, and up-to-date projects are
  skipped (`tsc -b --verbose` prints "up to date").
- The wiki suggests roughly 5 to 20 projects mirroring the dependency graph. References must form a
  DAG, and consumers do not see source edits until the referenced project is rebuilt.
- Since TypeScript 5.6 `--build` continues past errors in dependencies unless `--stopOnBuildErrors`
  is set.
- On tsc 7, `--builders N` builds independent projects concurrently and multiplies with
  `--checkers`; it does nothing on a chain of references.

## isolatedDeclarations and noCheck

- `isolatedDeclarations` (5.5+, needs `declaration` or `composite`) requires every export to be
  annotated enough to emit `.d.ts` without inference. Turning it on in tsc alone brings no speedup;
  the benefit comes from tools that emit declarations without type-checking, in parallel with the
  checker.
- Unannotated exports fail with `TS90xx` errors (for example `TS9013`). Add the annotations first;
  they are also explicit return types (below).
- `--noCheck` (5.6+) emits without type-checking. Run a separate `tsc --noEmit` so errors are still
  reported, and compare the output with a checked build when emit depends on types
  (`emitDecoratorMetadata`, cross-file `const enum`).

```sh
tsc -p . --noCheck        # emit only
tsc -p . --noEmit         # type errors, in parallel
```

## Explicit return types on exports

- An inferred exported return type is computed by the checker and written in full into `.d.ts`.
  Annotating it with a named interface shrinks declaration output and checker work.
- Do not annotate with a wider type (`object`, a base interface) to save time; consumers lose
  properties. Prove equality with a probe:
  `type Eq<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;` and assert
  `Eq<ReturnType<typeof before>, ReturnType<typeof after>>`.

## Large unions

- Values are compared with each member, and array literals of distinct members trigger pairwise
  subtype reduction. The wiki suggests a shared base interface past about a dozen object members.
- Do not use it where code narrows on a discriminant: a base type loses narrowing and
  exhaustiveness. Apply it only where a trace shows check time in files that build arrays of, or
  call functions typed with, the union.

## Intersections

- `interface T extends A, B` is one flattened, cached object type; `type T = A & B` is re-examined
  in relation checks and silently yields `never` for conflicting properties.
- It cannot extend unions, mapped types, or type parameters. The gain is small unless a trace
  already shows intersection relation checks.

## Recursive conditional types

- `TS2589` (excessively deep instantiation) on realistic input: make the recursive call the direct
  branch result and carry the result in an accumulator parameter. Since 4.5 that form is
  tail-evaluated; wrapping the call (`[0, ...Len<R>]`, `A | Get<R>`) disables it.

```ts
type Len<S extends string, A extends 0[] = []> =
  S extends `${string}${infer R}` ? Len<R, [0, ...A]> : A;
```

- Tail form only raises the limit. Bound user-supplied depth explicitly.

## Named conditional types

- The wiki advises naming inline conditional return types so they are cached. Measure before keeping
  it; the checker may already cache this. Apply it only if `Instantiations` falls on your own code.

[1]: https://github.com/microsoft/TypeScript/wiki/Performance
[2]: https://www.typescriptlang.org/tsconfig/
[3]: https://www.typescriptlang.org/docs/handbook/project-references.html
[4]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-5.html
[5]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html
[6]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-6.html
