# TypeScript and JavaScript

Read when replacing a branch chain, flag argument, string state, or long parameter list in
TypeScript or JavaScript. Check the repository's `typescript` version first; JavaScript has none of
the type-level checks below.

## Contents

- [Branch Chains](#branch-chains)
- [Lookup Tables](#lookup-tables)
- [Flag Arguments](#flag-arguments)
- [Guard Clauses](#guard-clauses)
- [Duplicated Branches](#duplicated-branches)
- [Primitive Obsession](#primitive-obsession)
- [Long Parameter Lists](#long-parameter-lists)
- [Dead Shims](#dead-shims)

## Branch Chains

Type the value as a union of string literals or a discriminated union, switch on it, and make the
default arm assign to `never`. A new member then fails to compile ([handbook][r1]).

```ts
type Shape = { kind: "circle"; r: number } | { kind: "square"; side: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.r ** 2;
    case "square":
      return shape.side ** 2;
    default: {
      const unreachable: never = shape;
      return unreachable;
    }
  }
}
```

Lint: `@typescript-eslint/switch-exhaustiveness-check` reports a `switch` over a literal union or
enum that misses a case and has no `default`. Its option `allowDefaultCaseForExhaustiveSwitch` set
to `false` flags a `default` on an already exhaustive switch ([rule][r2]). Fowler's name for the
object-oriented alternative is [Replace Conditional with Polymorphism][r3].

## Lookup Tables

Use a table when every arm only maps a key to a value. `satisfies Record<Kind, T>` (TypeScript 4.9)
errors on a missing or extra key and keeps the literal types ([release notes][r4]).

```ts
type Kind = "a" | "b";
const LABELS = { a: "Alpha", b: "Beta" } satisfies Record<Kind, string>;
```

Prefer `switch` when arms have side effects, `await`, or an early return, and avoid a plain
`Record<string, fn>`: it has no key check, and keys such as `toString` find inherited properties on
a plain object.

## Flag Arguments

Split into two functions (Fowler's [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html)) or take a string-literal union.
TypeScript has no named arguments, so `render(true)` is unreadable at the call site.

```ts
function renderCompact(doc: Doc): string { /* ... */ }
function renderFull(doc: Doc): string { /* ... */ }
```

## Guard Clauses

Plain early `return` or `throw`; there is no dedicated syntax. ESLint `no-else-return` flags an
`else` after a `return`, and `no-lonely-if` flags an `if` that is the only statement in an `else`.
`max-depth` limits nesting ([`no-else-return`](https://eslint.org/docs/latest/rules/no-else-return),
[`no-lonely-if`](https://eslint.org/docs/latest/rules/no-lonely-if),
[`max-depth`](https://eslint.org/docs/latest/rules/max-depth)). Fowler: [Replace Nested Conditional
with Guard Clauses][r5].

## Duplicated Branches

Fowler: [Consolidate Conditional Expression][r6] and [Slide
Statements](https://refactoring.com/catalog/slideStatements.html) to hoist shared lines. ESLint
`no-duplicate-case` catches a repeated `case` label, not a repeated body
([rule](https://eslint.org/docs/latest/rules/no-duplicate-case)). The research found no
TypeScript-specific rule for identical branch bodies.

## Primitive Obsession

For a closed set of strings use a literal union, not `string` ([literal types][r7]). A union of
literals works under `--erasableSyntaxOnly` (TypeScript 5.8), which rejects `enum` ([5.8
notes][r8]). A union `enum` also gives the checker the exact value set ([enums][r9]).

A type alias does not make a distinct type: "aliases are only aliases" ([handbook][r10]). For
`UserId` versus `OrderId`, a branded type such as `string & { __brand: "UserId" }` is a community
pattern; the handbook does not document it, so check the repository for an existing convention
before adding one. Fowler: [Replace Primitive with Object][r11].

## Long Parameter Lists

Take one object parameter and destructure it ([handbook][r12]). Fowler: [Introduce Parameter
Object][r13]. ESLint `max-params` reports the count
([rule](https://eslint.org/docs/latest/rules/max-params)).

```ts
interface SendOptions { to: string; subject: string; retries?: number }
function send({ to, subject, retries = 3 }: SendOptions): void { /* ... */ }
```

## Dead Shims

`/** @deprecated */` is recognized by the editor (TypeScript 4.0, [notes][r14]). Mark, then follow
[compatibility removal](compatibility-removal.md) before deleting.

[r1]: https://www.typescriptlang.org/docs/handbook/2/narrowing.html#exhaustiveness-checking
[r2]: https://typescript-eslint.io/rules/switch-exhaustiveness-check/
[r3]: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html
[r4]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html
[r5]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r6]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r7]: https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types
[r8]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html
[r9]: https://www.typescriptlang.org/docs/handbook/enums.html#union-enums-and-enum-member-types
[r10]: https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-aliases
[r11]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r12]: https://www.typescriptlang.org/docs/handbook/2/functions.html#parameter-destructuring
[r13]: https://refactoring.com/catalog/introduceParameterObject.html
[r14]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-0.html
