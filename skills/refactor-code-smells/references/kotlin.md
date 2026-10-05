# Kotlin

Read when replacing a branch chain, flag argument, primitive, or long parameter list in Kotlin.
Check the project's Kotlin version; each feature below names the release that added it.

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

"If you use `when` as an expression, you must cover all possible cases"; Boolean, enum, and sealed
subjects need no `else` ([docs][r1]). A `when` statement on an enum, sealed, or Boolean subject must
be exhaustive too: a warning in 1.6.0 and an error since 1.7.0 ([compatibility
guide](https://kotlinlang.org/docs/compatibility-guide-17.html)). Sealed classes and interfaces are
checked without `else`; in Kotlin Multiplatform common code, a `when` over an `expect` sealed class
still needs an `else` ([docs](https://kotlinlang.org/docs/sealed-classes.html)). Do not add `else`
to a closed subject.

```kotlin
enum class Mode { READ, WRITE }

fun label(mode: Mode): String = when (mode) {
    Mode.READ -> "r"
    Mode.WRITE -> "w"
}
```

Guard conditions in `when` branches (`is Cat if animal.mouseHunter ->`) are Stable in Kotlin 2.2
([what's new](https://kotlinlang.org/docs/whatsnew22.html)). Enums:
[docs](https://kotlinlang.org/docs/enum-classes.html). The research named no linter rule; the
compiler enforces this. Fowler: [Replace Conditional with Polymorphism][r2].

## Lookup Tables

`mapOf(Kind.A to ...)` or `EnumMap` loses `when` exhaustiveness. Prefer `when` for a closed enum.

## Flag Arguments

Named arguments fix the call site: the docs say it is "difficult to associate a value with an
argument, especially if it's null or a boolean value", and `reformat(s, normalizeCase = false)` is
readable ([docs](https://kotlinlang.org/docs/functions.html#named-arguments)). A named boolean is a
smaller smell; use an enum or two functions when the flag selects behavior (Fowler's [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html)).

## Guard Clauses

Use the elvis operator to exit early: `val name = person.name ?: return` or `?: throw ...`
([returns](https://kotlinlang.org/docs/returns.html), [null
safety](https://kotlinlang.org/docs/null-safety.html)). Non-local `break` and `continue` are Stable
in Kotlin 2.2. Fowler: [Replace Nested Conditional with Guard Clauses][r3].

## Duplicated Branches

A `when` branch lists several conditions separated by commas to share one body. Fowler: [Consolidate
Conditional Expression][r4]. The research found no linter rule for identical branch bodies.

## Primitive Obsession

A value class wraps a primitive as a distinct type; on the JVM it needs `value` plus `@JvmInline`
(stable in 1.5, [docs](https://kotlinlang.org/docs/inline-classes.html),
[1.5](https://kotlinlang.org/docs/whatsnew15.html)). Fowler: [Replace Primitive with Object][r5].

```kotlin
@JvmInline
value class Password(val s: String)
```

## Long Parameter Lists

Default parameter values cut overloads and named arguments label the rest; for a long list, a data
class of options is a reasonable parameter object (Fowler's [Introduce Parameter Object][r6]). The
research found no linter threshold to quote.

## Dead Shims

`@Deprecated(message, replaceWith = ReplaceWith(""), level = DeprecationLevel.WARNING)`; levels go
from warning to error to hidden ([API][r7]). Follow [compatibility
removal](compatibility-removal.md) before deleting.

[r1]: https://kotlinlang.org/docs/control-flow.html#when-expressions-and-statements
[r2]: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html
[r3]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r4]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r5]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r6]: https://refactoring.com/catalog/introduceParameterObject.html
[r7]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-deprecated/
