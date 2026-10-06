# Swift

Visibility, narrowest first: `private`, `fileprivate`,
`internal` (the default), `package`, `public`, `open`.
`private` at file scope already means file-wide,
so `fileprivate` is rarely needed there.
`package` is visible across the modules of one package,
so use it instead of `public` for declarations that only sibling targets call.
Use `open` only for a class that other modules must subclass.
Prefer a `struct` or `enum` to a class.
In Swift 6 language mode, mark public value types `Sendable`
and do not declare global mutable `var`s without isolation.

## Order in a file

1. Imports, with only the modules the file uses.
   Use `internal import` or `private import` for a module that is not part of the file's API.
1. File-level constants.
1. The main type, with its stored properties, initializers, then methods by role.
1. One `extension` per protocol conformance or concern, each after the type.
1. File-private types and helpers, last.

Tests go in `Tests/<Target>Tests` and use `@testable import` for `internal` access.

```swift
import Foundation

public let publicConstant = 1
let moduleConstant = 2
private let fileConstant = 3

public struct PublicType: Sendable {
    private var state = fileConstant

    public init() {}

    public func publicMethod() -> Int {
        privateMethod()
    }

    func moduleMethod() -> Int { moduleConstant }

    package func packageMethod() {}

    private func privateMethod() -> Int { state }
}

extension PublicType: CustomStringConvertible {
    public var description: String { "PublicType(\(state))" }
}

private struct PrivateType {
    func helper() {}
}
```
