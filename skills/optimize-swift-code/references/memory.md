# Value, ARC, and ownership constructs

These cards remove heap allocations, retain/release traffic, copies, and
runtime access checks. Pairs live in
`assets/examples/constructs/Sources/Constructs/Values.swift`; oracles in
`Sources/Catalog/Checks.swift` compare results, then use the malloc and
ARC counters from [measurement](measurement.md) to assert that the
candidate is cheaper. Counts are exact and come from
`sh assets/examples/verify.sh verify` (warm-up run first, second run
counted). Times are medians from `sh verify.sh time` on a shared Apple
M1 Max, Swift 6.3.3, `-O -wmo`; they are machine-specific.

## Contents

- Structs instead of classes for plain data
- Contiguous values instead of linked nodes
- Copy-on-write with isKnownUniquelyReferenced
- inout instead of copy and reassign
- consuming parameters
- The consume operator
- borrowing parameters
- Noncopyable types
- Local accumulator instead of a class property
- inout instead of a captured var
- Wrapping arithmetic

## Structs instead of classes for plain data

**Definition.** A struct stores its fields inline (in the array buffer,
on the stack); a class instance is a separate heap object with a
reference count. Value types without references need no retain/release
([Optimization tips][tips]).

**Use when.**

- A type is plain data (no identity, no shared mutation, no `deinit`)
  and is created in bulk or stored in arrays.

**Do not use when.**

- Callers rely on identity or shared mutation (`a === b`, one object
  updated through several references): a struct silently turns shared
  updates into independent copies.
- The value is large and copied often. The tips note the trade-off and
  suggest copy-on-write storage.
- The class never escapes a function: `-O` stack-promotes it anyway
  (measured: a non-escaping instance made 0 mallocs).

**Example.** Runnable: `Values.swift` (`makeObjects`, `makeValues`).

```swift
public final class PointObject {
    public let x: Int
    public let y: Int
    public init(x: Int, y: Int) { self.x = x; self.y = y }
}
public struct PointValue {
    public let x: Int
    public let y: Int
    public init(x: Int, y: Int) { self.x = x; self.y = y }
}
```

**Cost removed.** One heap allocation per element and ARC on access.
Measured: `ALLOC struct vs class construction: 1001 -> 1` (1,000 points);
summing 4,096 points 14823.3 ns -> 850.4 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS struct vs class result`
   and the `ALLOC` line.
1. Search the diff for `===`, shared references, and `deinit` on the
   converted type. Each is a semantic change.

## Contiguous values instead of linked nodes

**Definition.** Walking a class-based linked list moves a strong
reference from node to node: each hop retains the next node and
releases the previous one ([Optimization tips][tips], "Unsafe code"). A
contiguous buffer of values has no per-element reference counting.

**Use when.**

- A profile or the ARC counter shows `swift_retain`/`swift_release`
  proportional to the length of a traversal.

**Do not use when.**

- The structure needs O(1) insertion in the middle with stable node
  identity, and those operations dominate.
- The plan is `Unmanaged` references instead: the tips' example
  depends on `_withUnsafeGuaranteedRef`, which is "not a public API and
  will go away".

**Example.** Runnable: `Values.swift` (`sumList`, `sumListValues`).

```swift
@inline(never)
public func sumList(_ head: ListNode?) -> Int {
    var total = 0
    var current = head
    while let node = current {
        total &+= node.value
        current = node.next  // retain next, release previous
    }
    return total
}
```

**Cost removed.** Retains per hop. Measured: `RETAIN linked list vs array:
1002 -> 0`; package-benchmark `Retains` p50 1001 -> 0 and wall clock
14 µs -> 125 ns for 1,000 elements.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS linked list vs array`.
1. `sh assets/examples/verify.sh asm`: `sumList` has `_swift_retain`,
   `sumListValues` none.

## Copy-on-write with isKnownUniquelyReferenced

**Definition.** A struct that wraps class storage keeps value semantics
by copying the storage before a mutation only when it is shared.
[`isKnownUniquelyReferenced(&ref)`][cow-doc] returns `true` when the
object has exactly one strong reference ([Optimization tips][tips],
"Use copy-on-write semantics for large values").

**Use when.**

- A value type holds a class for storage (buffers, trees, caches) and
  either copies on every mutation (slow) or never copies (a
  value-semantics bug).

**Do not use when.**

- The storage is already a standard collection (`Array`, `Dictionary`,
  `String`): these implement copy-on-write. Wrap them directly.
- The reference is mutated from several threads without synchronization:
  the check "may still return `true`" under a data race.
- The storage contains `weak`/`unowned` references only: those do not
  count as strong references.

**Example.** Runnable: `Values.swift` (`AlwaysCopyVector`, `CowVector`).

```swift
public struct CowVector {
    var storage: Storage  // final class Storage { var values: [Int] }

    public mutating func set(_ index: Int, _ value: Int) {
        if !isKnownUniquelyReferenced(&storage) {
            storage = Storage(storage.values)
        }
        storage.values[index] = value
    }
}
```

**Cost removed.** A storage copy per mutation of an unshared value.
Measured: `ALLOC isKnownUniquelyReferenced: 1002 -> 2` (1,000 mutations);
256 mutations 15914.2 ns -> 2288.3 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS COW value semantics`
   (a copy mutated after assignment leaves the original unchanged).
1. The `ALLOC isKnownUniquelyReferenced` line shows the drop.

## inout instead of copy and reassign

**Definition.** `func f(_ a: [Int]) -> [Int] { var a = a; ...; return
a }` called as `x = f(x)` passes a second reference to the buffer, so
the mutation inside copies it; `inout` passes the storage itself
([Optimization tips][tips], "Use inplace mutation").

**Use when.**

- A hot helper takes a collection, mutates a local copy, and returns it
  to the same variable.

**Do not use when.**

- The caller needs both the old and the new value: the copy is the
  semantics.
- The argument is a class property or global used in the closure you
  pass alongside it: `inout` access to it overlaps and traps at run
  time (exclusivity).

**Example.** Runnable: `Values.swift` (`appendingOne`, `appendOne`).

```swift
@inline(never)
public func appendingOne(_ values: [Int]) -> [Int] {
    var copy = values
    copy.append(1)
    return copy
}

@inline(never)
public func appendOne(_ values: inout [Int]) {
    values.append(1)
}
```

**Cost removed.** A buffer copy per call. Measured: `ALLOC inout instead of
reassign: 1000 -> 9` (1,000 calls; 9 is normal geometric growth).

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal arrays and the `ALLOC`
   line.

## consuming parameters

**Definition.** A `consuming` parameter ([SE-0377][se377], Swift 5.9)
takes ownership of the argument: the callee destroys it and can mutate
it like a local `var`. When the caller's argument is at its last use,
ownership moves without a copy.

**Use when.**

- A function transforms and returns a value that callers reassign
  (`x = f(x)`), and changing the signature to `inout` does not fit (for
  example, a builder chain).
- An ordinary function stores or returns its argument: mark it
  `consuming`. Initializers and setters already consume by default.

**Do not use when.**

- The caller keeps using the argument: it must copy it first
  (implicitly for copyable types), so the saving disappears.
- The function only reads the argument: the default convention is
  already borrowed (+0) for ordinary functions.

**Example.** Runnable: `Values.swift` (`appendingOneConsuming`).

```swift
@inline(never)
public func appendingOneConsuming(_ values: consuming [Int]) -> [Int] {
    values.append(1)
    return values
}
// Caller: a = appendingOneConsuming(a)
```

**Cost removed.** The copy of a uniquely referenced buffer. Measured:
`ALLOC consuming parameter: 1000 -> 9` against the borrowed
`appendingOne` baseline.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal arrays and the `ALLOC`
   line.

## The consume operator

**Definition.** `consume x` ([SE-0366][se366], Swift 5.9) ends the
lifetime of a local binding and passes its value on; later uses of `x`
are compile errors.

**Use when.**

- The compiler cannot see that a use is the last one (the binding is
  used again on another path) and the ARC counter or allocation count
  shows a copy at that call.
- The compiler should reject accidental later uses of a moved value.

**Do not use when.**

- The call is already the last use. Measured:
  `a = appendingOneConsuming(a)` and
  `a = appendingOneConsuming(consume a)` both made 9 allocations for
  1,000 calls; the optimizer already moved the value.

**Example.** Runnable: `Checks.swift` (`consume operator` check).

```swift
var a = [1, 2, 3]
for _ in 0..<n { a = appendingOneConsuming(consume a) }
```

**Cost removed.** None measured in this shape (`ALLOC consume operator:
9 -> 9`, asserted equal).

**Verify.**

1. `sh assets/examples/verify.sh verify` prints the equal counts.

## borrowing parameters

**Definition.** A `borrowing` parameter ([SE-0377][se377]) is passed at
+0: the caller keeps ownership and the callee cannot consume or store
it without an explicit `copy`. Initializers and setters consume their
parameters by default, so a caller that keeps its value must retain it
for the call.

**Use when.**

- An initializer (or setter) only reads a parameter, and callers keep
  using the argument: the ARC counter shows a retain per call.

**Do not use when.**

- The initializer stores the parameter: storing needs `copy x`, which
  restores the retain. Keep the consuming default.
- An ordinary function: its parameters are already borrowed by default,
  so `borrowing` only forbids implicit copies there.

**Example.** Runnable: `Values.swift` (`Summary`).

```swift
public struct Summary: Equatable {
    public let count: Int
    public let total: Int

    @inline(never)
    public init(borrowing items: borrowing [Int]) {
        count = items.count
        var sum = 0
        for i in items.indices { sum &+= items[i] }
        total = sum
    }
}
```

**Cost removed.** A retain/release pair per call. Measured:
`RETAIN borrowing init: 8 -> 0` (8 inits of a kept array).

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal summaries and the
   `RETAIN` line.

## Noncopyable types

**Definition.** A `~Copyable` struct or enum ([SE-0390][se390], Swift
5.9) has exactly one owner: it cannot be copied implicitly, so it needs
no reference count, and its `deinit` runs once when the owner ends.
Parameters of noncopyable type must be `borrowing`, `consuming`, or
`inout`.

**Use when.**

- A class exists only to own a resource (a manually allocated buffer, a
  file descriptor) with a `deinit`, and the resource is never shared.

**Do not use when.**

- The value must go into `Array`, `Dictionary`, or other generic code
  that requires `Copyable`.
- The owner never escapes its function: `-O` already stack-promotes the
  class. Measured: allocation counts were equal (1 -> 1) until the owner
  was returned from a factory.
- The resource is shared by design: use a class.

**Example.** Runnable: `Values.swift` (`SharedBuffer`, `UniqueBuffer`).

```swift
public struct UniqueBuffer: ~Copyable {
    public let base: UnsafeMutablePointer<Int>
    public let count: Int
    public init(count: Int) {
        self.count = count
        base = .allocate(capacity: count)
        base.initialize(repeating: 0, count: count)
    }
    deinit { base.deallocate() }
}

@inline(never)
public func makeUnique(_ n: Int) -> UniqueBuffer {
    UniqueBuffer(count: n)
}
```

**Cost removed.** The owner object's allocation and its reference
counting. Measured: `ALLOC ~Copyable: 2 -> 1` (object + buffer versus
buffer); round trip for 64 elements 99.0 ns -> 59.2 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal sums and the `ALLOC`
   line.
1. Build with `-warnings-as-errors`: the compiler rejects any implicit
   copy of the noncopyable value.

## Local accumulator instead of a class property

**Definition.** Accesses to class stored properties, globals, static
properties, and escaping-closure captures get runtime exclusivity checks
(`swift_beginAccess`) in release builds ([exclusivity blog][excl]).
Reading the property into a local, working on the local, and writing it
back once limits the checks to two per call.

**Use when.**

- A profile shows `swift_beginAccess`/`swift_endAccess` inside a hot
  loop that updates a class property or global.

**Do not use when.**

- Code called inside the loop reads the property and expects the
  running value (callbacks, observers): the local defers the update and
  changes what they see.
- The assembly shows the access already outside the loop. Measured:
  `-O` widened `accumulateProperty`'s access to cover the whole loop
  even with an opaque closure call inside; the loop blocks contain no
  `swift_beginAccess`, and time was 14572.1 ns vs 14478.3 ns.

**Example.** Runnable: `Values.swift` (`accumulateProperty`,
`accumulateLocal`).

```swift
@inline(never)
public func accumulateLocal(_ acc: Accumulator, _ values: [Int]) {
    var total = acc.total
    for v in values {
        total &+= v
        progressHook(v)
    }
    acc.total = total
}
```

**Cost removed.** Per-iteration access checks where the optimizer could
not widen the access. Measured: none (see above).

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS exclusivity local
   accumulator`.
1. `sh assets/examples/verify.sh asm`: `accumulateProperty` loop has no
   `_swift_beginAccess`; if the real code's loop does, apply the card.

## inout instead of a captured var

**Definition.** A `var` captured by an escaping closure lives in a heap
box so the closure and its creator share it, "even [when] the
underlying type ... is trivial"; accesses through the box also get
dynamic exclusivity checks ([Optimization tips][tips]). Passing the
variable `inout` to a non-escaping function needs no box.

**Use when.**

- A closure is stored or passed as `@escaping` only for convenience,
  captures a local `var`, and the assembly shows `swift_allocObject`.

**Do not use when.**

- The closure really outlives the function (stored callback): the box
  is the semantics.

**Example.** Runnable: `Values.swift` (`countWithEscapingCapture`,
`countWithInout`).

```swift
@inline(never)
public func countWithInout(_ values: [Int]) -> Int {
    var matches = 0
    func visit(_ v: Int, _ count: inout Int) {
        if v > 0 { count += 1 }
    }
    for v in values { visit(v, &matches) }
    return matches
}
```

**Cost removed.** One box allocation per call plus its access checks.
Measured: `ALLOC inout instead of captured var: 1 -> 0`; assembly
`swift_allocObject` some -> none.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal counts for empty,
   mixed-sign, and 1,000-element inputs.
1. `sh assets/examples/verify.sh asm`: the `swift_allocObject`
   expectations.

## Wrapping arithmetic

**Definition.** `+`, `-`, `*` trap on overflow; `&+`, `&-`, `&*` wrap
around with fully defined results (`Int.max &+ 1 == Int.min`)
([Optimization tips][tips], [Advanced operators][adv-ops]).

**Use when.**

- Overflow is impossible by construction (bounded sums, indices) or
  wrapping is the intended result (hashes, checksums), and the assembly
  shows `b.vs` overflow branches in a hot loop.

**Do not use when.**

- Overflow is possible and must be reported: the trap is the error
  signal. Use `addingReportingOverflow` when the caller handles it.

**Example.** Runnable: `Values.swift` (`sumChecked`, `sumWrapping`).

```swift
@inline(never)
public func sumWrapping(_ values: [Int]) -> Int {
    var total = 0
    for v in values { total &+= v }
    return total
}
```

**Cost removed.** The overflow branch, which also blocked
vectorization. Measured assembly: `sumChecked` has 1 `b.vs` and no vector
adds; `sumWrapping` tail-calls a merged body with 7 `add.2d` vector
adds and no `b.vs`.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS wrapping arithmetic`
   (same sum when no overflow occurs).
1. `sh assets/examples/verify.sh asm`: `b.vs` some -> none.

[tips]: https://github.com/swiftlang/swift/blob/main/docs/OptimizationTips.rst
[cow-doc]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/ManagedBuffer.swift
[se377]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0377-parameter-ownership-modifiers.md
[se366]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0366-move-function.md
[se390]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0390-noncopyable-structs-and-enums.md
[excl]: https://www.swift.org/blog/swift-5-exclusivity/
[adv-ops]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/advancedoperators/
