# Swift

Read when replacing a branch chain, flag argument, primitive, or long parameter list in Swift. Check
the toolchain's Swift version; each feature below names the proposal that added it.

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

"Every `switch` statement must be exhaustive" ([book][r1]). A plain `default` makes it exhaustive
but hides new cases, so name every case on an enum you own. For a non-frozen enum from another
module "you always need to include a default case"; write `@unknown default:`, which "should match
only enumeration cases that are added in the future" and warns if it matches a known case (SE-0192,
Swift 5.0, [book][r2], [proposal][r3]).

`switch` is an expression when each branch is one expression (SE-0380, Swift 5.9, [proposal][r4]).

```swift
let label = switch mode {
case .read: "r"
case .write: "w"
}
```

Enums take raw values for string state and associated values for sum types ([book][r5]). The
research did not name a linter rule for this smell; the compiler enforces it. Fowler: [Replace
Conditional with Polymorphism][r6].

## Lookup Tables

A `[Kind: String]` dictionary returns an `Optional` and loses `switch` exhaustiveness. Prefer a
`switch` over a `CaseIterable` enum.

## Flag Arguments

"The argument label is used when calling the function", so `send(urgent: true)` is readable
([book][r7]). The smell is mainly an unlabeled `_ flag: Bool`. Label it, or split into two functions
or an enum (Fowler's [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html)).

## Guard Clauses

`guard` "always has an `else` clause" that must transfer control ([book][r8]). `if let x {`
shorthand (SE-0345, Swift 5.7, [proposal][r9]) shortens the unwrap. Fowler: [Replace Nested
Conditional with Guard Clauses][r10].

```swift
guard let name = person["name"] else { return }
```

## Duplicated Branches

A `case` lists several patterns separated by commas to share one body. Fowler: [Consolidate
Conditional Expression][r11]. The research found no linter rule for identical branch bodies.

## Primitive Obsession

Wrap the value in a struct, or use a `RawRepresentable` enum for a closed set (the Swift book
chapter "Structures and Classes"). Fowler: [Replace Primitive with Object][r13].

```swift
struct UserID: Hashable { let raw: Int }
```

## Long Parameter Lists

Give parameters default values to cut the list, and group related ones in a struct (Fowler's
[Introduce Parameter Object][r14]). The research found no Swift linter threshold to quote.

## Dead Shims

`@available(*, deprecated, message:)` and `obsoleted:` ([book][r15]). Follow [compatibility
removal](compatibility-removal.md) before deleting.

[r1]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/controlflow/
[r2]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/statements/
[r3]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0192-non-exhaustive-enums.md
[r4]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0380-if-switch-expressions.md
[r5]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/enumerations/
[r6]: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html
[r7]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/functions/
[r8]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/controlflow/
[r9]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0345-if-let-shorthand.md
[r10]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r11]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r13]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r14]: https://refactoring.com/catalog/introduceParameterObject.html
[r15]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/attributes/
