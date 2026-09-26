# Type-level constructs

Each card changes how much work the type checker does for the same
program. The oracle in `checker-cases.ts` generates baseline and candidate
fixtures, runs `tsc --singleThreaded --extendedDiagnostics`, requires both
to type-check (or proves the documented failure), and asserts a counter
that is identical across runs (`Types`, `Instantiations`, `Memory used`, `.d.ts`
bytes). Run `sh assets/examples/verify.sh checker`.

Local numbers: tsc 7.0.2, Apple M1 Max, macOS, `--singleThreaded
--skipLibCheck`. Counters repeated exactly across runs; `Memory used`
varied by less than 1%. `Check time` comes from a shared machine and is
reported, never asserted. See [measurement](measurement.md) for the
counters.

Tier: Executed (`verify.sh checker`; timings from `verify.sh measure`).

## Contents

- Base type instead of a large union
- Interfaces instead of intersections
- Tail-recursive conditional types
- Named conditional types
- Explicit return types on exports

## Base type instead of a large union

**Definition.** Checking a value against a union compares it with each
member, and array literals of distinct members trigger subtype reduction,
which compares members pairwise; a shared base interface is one
comparison ([Performance wiki][wiki], "Preferring Base Types Over
Unions").

**Use when.**

- A union has more than about a dozen object members (the wiki's
  threshold) and values flow where the whole union is expected.
- A trace shows `structuredTypeRelatedTo` or check time concentrated in
  files that build arrays or call functions typed with that union.

**Do not use when.**

- Code narrows on a discriminant (`switch (e.kind)`): a base type loses
  exhaustiveness checking and narrowing.
- The union is small: the cost scales with the member count.

**Example.**

```typescript
export interface EvBase {
  at: number;
}
export interface Ev0 extends EvBase {
  p0: string;
}
// ... Ev1 .. Ev299
declare function handle(e: EvBase): void; // baseline: (e: Ev0 | ... | Ev299)
```

Runnable: `unionSources()` in `assets/examples/checker-cases.ts` (300
members, 600 calls, 600 array literals).

**Cost removed.** Pairwise relation checks. Local: `Memory used` 52,261K
to 30,407K, `Types` 3,094 to 2,794; `Check time` median 0.33-0.57 s vs
0.04-0.10 s (three shared-machine runs).

**Verify.**

1. Behavior: both fixtures type-check with zero errors. For real code,
   run the type tests and confirm narrowing sites still compile.
1. Benefit: `METRIC base-type Memory used K` and `METRIC base-type Types`
   decrease; `verify.sh measure` prints `TIME check gen/union.ts`.

## Interfaces instead of intersections

**Definition.** `interface T extends A, B` creates one flattened object
type whose relations are cached; `type T = A & B` keeps an intersection
that is re-examined in relation checks ([Performance wiki][wiki],
"Preferring Interfaces Over Intersections").

**Use when.**

- Object types are composed from several named object types and are
  compared often (parameters, return types).
- Property conflicts should be reported at the declaration: interfaces
  report them, while intersections silently produce `never` members.

**Do not use when.**

- The composition includes a union, a mapped type, or a type parameter:
  interfaces can only extend object types with statically known members.

**Example.**

```typescript
interface B0 {
  k0: number;
  s0: string;
}
// baseline: type T0 = B0 & B1 & ... & B11 & { own0: string };
interface T0 extends B0, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11 {
  own0: string;
}
export function f0(x: T0): S0 {
  return x;
}
```

Runnable: `intersections()` in `checker-cases.ts` (400 composed types of
12 members each).

**Cost removed.** Intermediate intersection types. Local: `Types` 1,345 to
945. `Check time` did not move measurably at this size (0.014-0.036 s
both ways) on tsc 7.0.2. Expect a benefit only when a profile already
shows relation checks on intersections.

**Verify.**

1. Behavior: both fixtures type-check with zero errors.
1. Benefit: `METRIC interfaces Types: 1345 -> 945`.

## Tail-recursive conditional types

**Definition.** Since TypeScript 4.5, a conditional type whose branch is
directly another instantiation of itself is evaluated without
intermediate instantiations and with a much higher recursion allowance;
wrapping the recursive call (`[0, ...Len<R>]`, `A | Get<R>`) disables
that ([TypeScript 4.5][ts45]).

**Use when.**

- A recursive type reports `TS2589: Type instantiation is excessively deep
  and possibly infinite` on realistic inputs.
- The recursion builds a result (tuple, union, string) that can be carried
  in an accumulator type parameter.

**Do not use when.**

- The recursion depth is unbounded or user-supplied: bound it
  explicitly, because tail recursion only raises the limit.

**Example.**

```typescript
// baseline: S extends `${string}${infer R}` ? [0, ...Len<R>] : [];
type Len<S extends string, A extends 0[] = []> =
  S extends `${string}${infer R}` ? Len<R, [0, ...A]> : A;

export const length: Len<S100>["length"] = 100;
```

Runnable: `assets/examples/checker/non-tail.ts` and `checker/tail.ts`
(100-character string).

**Cost removed.** A failed type check. Local: the baseline fails with
`TS2589`; the candidate type-checks (with more `Instantiations`, 479 to
933, because it completes).

**Verify.**

1. Behavior: the candidate's assertion `Len<S100>["length"] = 100`
   compiles, so the computed type is correct.
1. Benefit: the oracle asserts `TS2589` for the baseline and zero errors
   for the candidate.

## Named conditional types

**Definition.** The wiki recommends moving an inline conditional return
type into a named alias so the checker can cache it
([Performance wiki][wiki], "Using Type Annotations" and "Naming Complex
Types").

**Use when.**

- A trace or the `Instantiations` count shows the same conditional type
  re-evaluated on a hot generic call.

**Do not use when.**

- No counter shows re-evaluation: on tsc 7.0.2 the local fixture (2,000
  calls of a generic with a two-level conditional return type) showed no
  benefit: `Instantiations` 19 (inline) vs 33 (named), `Check time` equal.
  The checker already caches instantiations by type arguments.

**Example.**

```typescript
type Wrap<U> = U extends string
  ? { s: U }
  : U extends number
    ? { n: U }
    : Box<U>;
function f<U>(x: U): Wrap<U> {
  return x as Wrap<U>;
}
```

Runnable: `conditionals()` in `checker-cases.ts`.

**Cost removed.** None measured locally. This card is a counter-check on
the wiki advice for tsc 7.

**Verify.**

1. Behavior: both fixtures type-check with zero errors.
1. Benefit: the oracle prints
   `REPORT named-conditional: no benefit asserted` with both counts. Apply
   the change only if your own fixture shows `Instantiations` falling.

## Explicit return types on exports

**Definition.** An exported function's inferred return type must be
computed by the checker and written in full into `.d.ts`; an annotated
return type naming an interface is emitted as that name
([Performance wiki][wiki], "Using Type Annotations").

**Use when.**

- `declaration: true` and `.d.ts` files repeat large anonymous object
  types.
- A project plans `isolatedDeclarations`, which requires the annotations
  anyway (see [build](build.md#isolated-declarations-with-nocheck)).

**Do not use when.**

- The annotation would widen the type (`object`, a base type):
  consumers lose properties. The oracle checks mutual assignability to
  catch this.

**Example.**

```typescript
export interface Rec0 extends Rec {
  k0: number;
}
export function get0(n: number): Rec0 {
  return { ...base(n), k0: n };
}
// baseline: export function get0(n: number) { ... }  (inferred)
```

Runnable: `returnTypes()` in `checker-cases.ts` (200 exports).

**Cost removed.** Declaration size and checker types. Local: `.d.ts`
53,180 B to 21,602 B; `Types` 1,895 to 1,099.

**Verify.**

1. Behavior: `gen/ret/probe.ts` asserts
   `Eq<ReturnType<typeof I.get0>, ReturnType<typeof A.get0>>` is `true`
   for all 200 functions and must type-check.
1. Benefit: `METRIC return-types .d.ts bytes: 53180 -> 21602`.

[wiki]: https://github.com/microsoft/TypeScript/wiki/Performance
[ts45]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-5.html
