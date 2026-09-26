# Dispatch constructs

These cards turn indirect calls (vtable, witness table, Objective-C
message send, cross-module call) into direct or inlined calls. Pairs live
in `assets/examples/constructs/Sources/Constructs/Dispatch.swift`;
`sh assets/examples/verify.sh asm` asserts the call patterns and
`verify` asserts equal results.

`-O` with WMO **already optimized** several baselines here: it
specialized existential parameters with a visible concrete argument and
inlined cross-module calls inside one SwiftPM graph. Those cards say so.
Keep a rewrite only where the real build's assembly still shows the
indirect call. Measured on an Apple M1 Max, Swift 6.3.3, `-O -wmo`,
shared machine; numbers are machine-specific.

## Contents

- final classes and members
- Access control that lets WMO infer final
- Avoiding @objc dynamic
- Generic specialization instead of any P parameters
- Generic stored property instead of a stored existential
- Enum instead of an array of existentials
- @inlinable, @usableFromInline, and @frozen across modules
- Class-constrained protocols

## final classes and members

**Definition.** `final` on a class or member forbids overriding, so a
call through that static type has one target. The compiler emits a
direct call, which it can inline, instead of a vtable lookup
([Optimization tips][tips]).

**Use when.**

- The assembly or SIL of a hot loop shows `blr`/`class_method` calls on
  a class that has no subclasses.
- The class is `public` and consumers must not subclass it anyway.

**Do not use when.**

- A subclass exists or a public library's clients may subclass: adding
  `final` breaks them.
- Tests subclass the type for mocking.
- The class is `internal` or `private` and the module builds with WMO:
  the compiler already infers `final` (next card).

**Example.** Runnable: `Dispatch.swift` (`totalAreaOpen`,
`totalAreaFinal`).

```swift
public class Shape {
    public init() {}
    public func area() -> Int { 1 }
}
public class Square: Shape {  // subclass exists: vtable call
    let side: Int
    public init(side: Int) { self.side = side }
    override public func area() -> Int { side &* side }
}
public final class FinalSquare {
    let side: Int
    public init(side: Int) { self.side = side }
    public func area() -> Int { side &* side }
}
```

**Cost removed.** One indirect call per element. Measured SIL:
`totalAreaOpen` 1 `class_method`, `totalAreaFinal` 0; assembly: 1 `blr`
versus 0. Time for 4,096 elements: 17346.7 ns -> 14914.6 ns (median of
31, noisy machine).

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS final`.
1. `sh assets/examples/verify.sh asm`: the `SIL totalAreaOpen` line
   (`class_method` 1 -> 0) and the two `blr` expectations.

## Access control that lets WMO infer final

**Definition.** `private` and `fileprivate` declarations are visible in
one file, and under WMO the compiler sees every use of `internal`
declarations. It can then prove no override exists and infer `final`
([Optimization tips][tips]).

**Use when.**

- A class or member is `public` or `open` only by habit: making it
  `internal` or narrower removes dynamic dispatch without a keyword.

**Do not use when.**

- The build is not WMO (per-file compilation): SIL keeps `class_method`
  for internal classes used from another file
  ([WMO card](build-settings.md#whole-module-optimization)).
- Another module needs the declaration.

**Example.** Runnable: `Dispatch.swift` (`tallyInternal`).

```swift
class Tally {  // internal, no subclass in the module
    var count = 0
    func bump(_ by: Int) { count &+= by }
}

@inline(never)
public func tallyInternal(_ values: [Int]) -> Int {
    let tally = Tally()
    for v in values { tally.bump(v) }
    return tally.count
}
```

**Cost removed.** The vtable call: `tallyInternal` has 0 `blr` under WMO
(and the object is stack-promoted). Per-file compilation of the
`wmo/` demo keeps 2 `class_method` instructions.

**Verify.**

1. `sh assets/examples/verify.sh asm`: `tallyInternal` has no `blr`.
1. `sh assets/examples/verify.sh wmo`: `class_method` 2 -> 0.

## Avoiding @objc dynamic

**Definition.** `dynamic` makes Swift "emit calls via Objective-C message
send" (`objc_msgSend`), which blocks inlining and devirtualization
([Optimization tips][tips]). `@objc` alone exposes a method to
Objective-C; Swift callers still use Swift dispatch.

**Use when.**

- A hot path calls `@objc dynamic` members that no KVO observer,
  method swizzling, or Objective-C subclass relies on.

**Do not use when.**

- Key-value observing of the property is used (KVO requires `@objc
  dynamic`), or the method is swizzled or replaced at run time.
- The type must stay an `NSObject` subclass for an Objective-C API;
  remove only `dynamic`, then re-check the assembly.

**Example.** Runnable: `Dispatch.swift` (`countLegacy`, `countSwift`).

```swift
public class LegacyCounter: NSObject {
    @objc dynamic public func step() -> Int { 1 }
}
public final class SwiftCounter {
    public init() {}
    public func step() -> Int { 1 }
}
```

**Cost removed.** One message send per call. Measured assembly:
`countLegacy` has 1 `objc_msgSend` in its loop, `countSwift` none (the
loop folds to `n`). Time for 4,096 calls: 10575.4 ns -> 2.1 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS @objc dynamic`.
1. `sh assets/examples/verify.sh asm`: `objc_msgSend` some -> none.

## Generic specialization instead of any P parameters

**Definition.** A `some P` parameter ([SE-0341][se341]) is sugar for a
generic parameter: with the body visible, `-O` emits a copy specialized
for the concrete type (symbol suffix `Tg5`) with direct calls. An
`any P` parameter is an existential box ([SE-0335][se335]); calls go
through the witness table unless the optimizer specializes it.

**Use when.**

- A public or cross-module API takes `any P` and callers pass concrete
  types, while the assembly of the callee shows `blr` witness calls.

**Do not use when.**

- Callers store mixed types; see the enum and stored-generic cards.
- The call site is in the same module with a concrete argument. Measured:
  `-O` specialized the `any` version too and merged `callAny` and
  `callSome` into one identical function with no `blr`; 330.8 ns vs
  345.4 ns.
- Code size matters more: each specialization is a separate copy.

**Example.** Runnable: `Dispatch.swift`.

```swift
public protocol Scorer { func score(_ x: Int) -> Int }

@inline(never)
public func totalScoreAny(_ scorer: any Scorer, _ xs: [Int]) -> Int {
    xs.reduce(0) { $0 &+ scorer.score($1) }
}

@inline(never)
public func totalScoreSome(_ scorer: some Scorer, _ xs: [Int]) -> Int {
    xs.reduce(0) { $0 &+ scorer.score($1) }
}
```

**Cost removed.** A witness-table call per element where the optimizer
did not already specialize. Measured: nothing, for the reason above.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS some vs any`.
1. `sh assets/examples/verify.sh asm`: `callAny` and `callSome` both have
   no `blr` (records the no-difference result).

## Generic stored property instead of a stored existential

**Definition.** A stored `let scorer: any Scorer` keeps the box and its
witness table, so every method using it dispatches dynamically. A generic
struct `Scored<S: Scorer>` stores the concrete type, so methods of
`Scored<Doubler>` are specialized.

**Use when.**

- A long-lived object (pipeline, parser, strategy holder) stores a
  protocol-typed dependency and calls it per element.

**Do not use when.**

- The dependency is swapped at run time among types the compiler cannot
  see, or the generic parameter would leak into many public signatures.

**Example.** Runnable: `Dispatch.swift` (`ScoredAny`, `Scored`).

```swift
public struct ScoredAny {
    let scorer: any Scorer
    @inline(never)
    public func total(_ xs: [Int]) -> Int {
        xs.reduce(0) { $0 &+ scorer.score($1) }
    }
}
public struct Scored<S: Scorer> {
    let scorer: S
    @inline(never)
    public func total(_ xs: [Int]) -> Int {
        xs.reduce(0) { $0 &+ scorer.score($1) }
    }
}
```

**Cost removed.** One witness call per element: `ScoredAny.total` has 1
`blr`; `pipelineGeneric` calls a `Tg5` specialization and has none.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS generic stored property`.
1. `sh assets/examples/verify.sh asm`: `ScoredAny.total` blr,
   `pipelineGeneric` no blr and a `Tg5` callee.

## Enum instead of an array of existentials

**Definition.** `[any P]` stores boxes of possibly different types, and
each call dispatches through the element's witness table. When the set
of conforming types is closed, an enum with one case per type
dispatches with a `switch`, which the compiler can inline.

**Use when.**

- A hot loop iterates `[any P]` whose element types come from a fixed
  list inside the module.

**Do not use when.**

- Other modules add conformances (plugins, public protocols): an enum
  cannot represent them.
- The protocol has many requirements: every one needs a `switch`.

**Example.** Runnable: `Dispatch.swift` (`totalMixedAny`,
`totalMixedEnum`).

```swift
public enum KnownScorer {
    case doubler(Doubler)
    case tripler(Tripler)

    @inline(__always)
    func score(_ x: Int) -> Int {
        switch self {
        case .doubler(let d): d.score(x)
        case .tripler(let t): t.score(x)
        }
    }
}
```

**Cost removed.** The indirect call and existential projection per
element: `totalMixedAny` 1 `blr`, `totalMixedEnum` 0.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS enum instead of [any P]`.
1. `sh assets/examples/verify.sh asm`: blr some -> none.

## @inlinable, @usableFromInline, and @frozen across modules

**Definition.** `@inlinable` makes a public function's body part of the
module interface so clients can inline and specialize it;
`@usableFromInline` lets such a body use an `internal` declaration
([SE-0193][se193]). Under library evolution a struct's layout is
resilient unless `@frozen` ([SE-0260][se260]); only delegating
initializers of a non-frozen struct can be `@inlinable` (SE-0193).

**Use when.**

- The callee module is built with `-enable-library-evolution` (binary
  frameworks, SDK-style libraries) and the client's assembly shows calls
  into small functions.

**Do not use when.**

- Both modules build from source in one SwiftPM graph: default CMO
  already inlines (see [CMO][cmo]).
- The body can change after release: clients keep the old inlined copy
  until recompiled, so `@inlinable` and `@frozen` are ABI promises.

**Example.** Runnable: `assets/examples/constructs/Sources/Helper/`
`Helper.swift`.

```swift
@inlinable
public func helperScaleInlinable(_ x: Int) -> Int { x &* 3 &+ 1 }

@frozen
public struct Meter {
    @usableFromInline var raw: Int
    @inlinable public init(_ raw: Int) { self.raw = raw }
    @inlinable public var scaled: Int { raw &* 3 &+ 1 }
}
```

Without `@frozen`, the compiler rejects the `@inlinable` root
initializer ("'self' used before 'self.init' call"). With a plain
`public init`, the client still called `Meter`'s metadata accessor,
initializer, and `raw` getter (3 calls plus a `blr`).

**Cost removed.** The cross-module call per element. Library-evolution
build: `scaleAllOpaque` 1 call to `helperScale`; `scaleAllInlinable` and
`scaleAllMeters` 0 references to `Helper`.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS @inlinable` and
   `PASS @usableFromInline`.
1. `sh assets/examples/verify.sh asm`: the three `evo.s` expectations.

## Class-constrained protocols

**Definition.** `protocol P: AnyObject` restricts conformers to classes,
so an `any P` is a single object reference plus witness table and ARC
can treat it as a class reference ([Optimization tips][tips]).

**Use when.**

- Only classes adopt the protocol, and callers need `weak` references
  or identity (`===`): those require the constraint.

**Do not use when.**

- The goal is fewer retains. Measured on Swift 6.3.3: `pingAll`
  (`[any Pinger]`) and `pingAllClassBound` (`[any ClassPinger]`) both
  made 2000 retains for 1000 elements and both keep one `blr` per
  element.
- Value types must conform.

**Example.** Runnable: `Dispatch.swift` (`pingAll`,
`pingAllClassBound`).

```swift
public protocol ClassPinger: AnyObject {
    func ping() -> Int
}
```

**Cost removed.** None measured (see above). The class-bound version
used `swift_unknownObjectRetain` instead of an outlined existential
copy.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints
   `RETAIN AnyObject protocol: 2000 -> 2000`.

[tips]: https://github.com/swiftlang/swift/blob/main/docs/OptimizationTips.rst
[se335]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0335-existential-any.md
[se341]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0341-opaque-parameters.md
[se193]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0193-cross-module-inlining-and-specialization.md
[se260]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0260-library-evolution.md
[cmo]: build-settings.md#cross-module-optimization-and-library-evolution
