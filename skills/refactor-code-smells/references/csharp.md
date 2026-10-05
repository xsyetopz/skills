# C Sharp

Read when replacing a branch chain, flag argument, primitive, or long parameter list in C#. Check
the project's `LangVersion` first; each feature below names the C# version that added it.

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

Use a switch expression: the compiler warns "if a switch expression doesn't handle all possible
input values", and at run time an unmatched value throws `SwitchExpressionException`. List patterns
do not warn ([docs][r1]).

```csharp
string Label(Mode mode) => mode switch
{
    Mode.Read => "r",
    Mode.Write => "w",
};
```

The compiler warnings (Microsoft Learn, "Pattern matching warnings") are:

- CS8509: the switch expression is not exhaustive.
- CS8524: it misses an unnamed enum value such as `(Mode)10`; a discard `_` arm covers it.
- CS8846: a `when` clause may hide a match.
- CS8510: an arm is unreachable.

Keep these warnings on; do not add `_` to silence CS8509 on an enum you own. In C# 15 (preview in
.NET 11) `public union Pet(Cat, Dog, Bird);` makes a switch expression exhaustive over its case
types with no catch-all arm ([docs][r3]). Fowler: [Replace Conditional with Polymorphism][r4].

## Lookup Tables

A `Dictionary<Mode, T>` or `FrozenDictionary` loses CS8509, so a new enum member compiles silently.
Prefer the switch expression for a closed enum.

## Flag Arguments

Named arguments (C# 4) "improve the readability of your code", so `Send(urgent: true)` is a
smaller smell (Microsoft Learn, "Named and optional arguments"). With two or more bool parameters,
use an enum or separate methods (Fowler's [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html)).

## Guard Clauses

Early `return` or `throw`; `if (x is not Foo f) return;` uses the `is not` pattern (C# 9,
[patterns][r6]). Fowler: [Replace Nested Conditional with Guard Clauses][r7].

```csharp
if (shape is not Circle circle) return 0;
return circle.Radius;
```

## Duplicated Branches

Relational and logical patterns (`or`, `and`, `not`) merge arms that share a body (C# 9, patterns
page above). Fowler: [Consolidate Conditional Expression][r8]. The research found no analyzer rule
for identical branch bodies.

## Primitive Obsession

A `readonly record struct` is a value type with value equality (C# 10, [docs][r9]). Records are C# 9
([docs][r10]). For a closed string set use an `enum`. Fowler: [Replace Primitive with Object][r11].

```csharp
public readonly record struct UserId(Guid Value);
```

## Long Parameter Lists

Use a record or class of options with `required` members (C# 11): they "must be initialized by an
object initializer" ([docs][r12]). Fowler: [Introduce Parameter Object][r13].

```csharp
public sealed record SendOptions
{
    public required string To { get; init; }
    public int Retries { get; init; } = 3;
}
```

## Dead Shims

`[Obsolete("msg", error: true)]` ([docs][r14]) turns uses into errors before removal. Follow
[compatibility removal](compatibility-removal.md) before deleting.

[r1]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/switch-expression
[r3]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/union
[r4]: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html
[r6]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/patterns
[r7]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r8]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r9]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/struct
[r10]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/record
[r11]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r12]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/required
[r13]: https://refactoring.com/catalog/introduceParameterObject.html
[r14]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/attributes/general
