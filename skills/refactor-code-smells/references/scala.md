# Scala

Read when replacing a branch chain, flag argument, primitive, or long parameter list in Scala 3.
Check the project's Scala version: 3.3 LTS and 3.9 LTS are the long-term releases listed on
[scala-lang.org](https://www.scala-lang.org/download/all.html).

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

Use an `enum` ([docs][r1]; with parameters,
[ADTs](https://docs.scala-lang.org/scala3/reference/enums/adts.html)) and `match`. Error E029 is
"emitted when a pattern match expression may not handle all possible input values"; E030 marks an
unreachable case ([E029][r2]). Do not add `case _` on an enum you own, since it hides the check. New
control syntax allows `if x < 0 then ... else if` without braces ([docs][r3]).

```scala
enum Mode:
  case Read, Write

def label(mode: Mode): String = mode match
  case Mode.Read  => "r"
  case Mode.Write => "w"
```

The research named no linter rule; the compiler warns. Fowler: [Replace Conditional with
Polymorphism][r4].

## Lookup Tables

A `Map[Kind, T]` loses exhaustivity; prefer `match` on the enum.

## Flag Arguments

Named arguments "can be written in any order" and make `render(compact = true)` readable; once one
is out of order, the rest must be named
([tour](https://docs.scala-lang.org/tour/named-arguments.html)). With two or more flags, use an enum
or separate methods (Fowler's [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html)).

## Guard Clauses

`scala.util.boundary` with `break(value)` replaces non-local `return` (3.3): "A boundary that can be
exited by break calls" ([API](https://www.scala-lang.org/api/3.x/scala/util/boundary$.html)).
Fowler: [Replace Nested Conditional with Guard Clauses][r5].

```scala
import scala.util.boundary, boundary.break

def firstEven(xs: List[Int]): Option[Int] = boundary:
  for x <- xs do if x % 2 == 0 then break(Some(x))
  None
```

## Duplicated Branches

Fowler: [Consolidate Conditional Expression][r6]. The research found no Scala-specific rule or
syntax for identical branch bodies.

## Primitive Obsession

An opaque type is `opaque type Logarithm = Double` "without any overhead" and is seen as abstract
outside the defining scope ([docs][r7]). Fowler: [Replace Primitive with Object][r8].

```scala
object ids:
  opaque type UserId = Int
  def UserId(n: Int): UserId = n
```

## Long Parameter Lists

Named arguments label the call. Named tuples (3.7+) give a lightweight record, `type Person = (name:
String, age: Int)` ([docs][r9]). A case class of options with default values is a reasonable
parameter object (Fowler's [Introduce Parameter Object][r10]). The research found no linter
threshold to quote.

## Dead Shims

`@deprecated("msg", since)` ([API](https://www.scala-lang.org/api/3.x/scala/deprecated.html)).
Follow [compatibility removal](compatibility-removal.md) before deleting.

[r1]: https://docs.scala-lang.org/scala3/reference/enums/enums.html
[r2]: https://docs.scala-lang.org/scala3/reference/error-codes/E029.html
[r3]: https://docs.scala-lang.org/scala3/reference/other-new-features/control-syntax.html
[r4]: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html
[r5]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r6]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r7]: https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html
[r8]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r9]: https://docs.scala-lang.org/scala3/reference/other-new-features/named-tuples.html
[r10]: https://refactoring.com/catalog/introduceParameterObject.html
