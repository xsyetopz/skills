// Dispatch constructs: final, access-control-inferred final, generics vs
// existentials, class-bound protocols, @objc dynamic, cross-module calls.
import Foundation
import Helper

// MARK: final

public class Shape {
  public init() {}
  public func area() -> Int { 1 }
}

public class Square: Shape {
  let side: Int
  public init(side: Int) { self.side = side }
  override public func area() -> Int { side &* side }
}

public final class FinalSquare {
  let side: Int
  public init(side: Int) { self.side = side }
  public func area() -> Int { side &* side }
}

@inline(never)
public func totalAreaOpen(_ shapes: [Shape]) -> Int {
  shapes.reduce(0) { $0 &+ $1.area() }
}

@inline(never)
public func totalAreaFinal(_ shapes: [FinalSquare]) -> Int {
  shapes.reduce(0) { $0 &+ $1.area() }
}

// MARK: internal class, no subclasses in the module (inferred final)

class Tally {
  var count = 0
  func bump(_ by: Int) { count &+= by }
}

@inline(never)
public func tallyInternal(_ values: [Int]) -> Int {
  let tally = Tally()
  for v in values { tally.bump(v) }
  return tally.count
}

// MARK: generics (specialized) vs existentials (any P)

public protocol Scorer {
  func score(_ x: Int) -> Int
}

public struct Doubler: Scorer {
  public init() {}
  public func score(_ x: Int) -> Int { x &* 2 }
}

public struct Tripler: Scorer {
  public init() {}
  public func score(_ x: Int) -> Int { x &* 3 }
}

@inline(never)
public func totalScoreAny(_ scorer: any Scorer, _ xs: [Int]) -> Int {
  xs.reduce(0) { $0 &+ scorer.score($1) }
}

@inline(never)
public func totalScoreSome(_ scorer: some Scorer, _ xs: [Int]) -> Int {
  xs.reduce(0) { $0 &+ scorer.score($1) }
}

@inline(never)
public func callAny(_ xs: [Int]) -> Int {
  totalScoreAny(Doubler(), xs)
}

@inline(never)
public func callSome(_ xs: [Int]) -> Int {
  totalScoreSome(Doubler(), xs)
}

// MARK: stored existential vs generic parameter

public struct ScoredAny {
  let scorer: any Scorer
  public init(_ scorer: any Scorer) { self.scorer = scorer }

  @inline(never)
  public func total(_ xs: [Int]) -> Int {
    xs.reduce(0) { $0 &+ scorer.score($1) }
  }
}

public struct Scored<S: Scorer> {
  let scorer: S
  public init(_ scorer: S) { self.scorer = scorer }

  @inline(never)
  public func total(_ xs: [Int]) -> Int {
    xs.reduce(0) { $0 &+ scorer.score($1) }
  }
}

@inline(never)
public func pipelineAny(_ xs: [Int]) -> Int {
  ScoredAny(Doubler()).total(xs)
}

@inline(never)
public func pipelineGeneric(_ xs: [Int]) -> Int {
  Scored(Doubler()).total(xs)
}

// MARK: heterogeneous [any P] vs enum of known cases

@inline(never)
public func totalMixedAny(_ scorers: [any Scorer], _ x: Int) -> Int {
  scorers.reduce(0) { $0 &+ $1.score(x) }
}

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

@inline(never)
public func totalMixedEnum(_ scorers: [KnownScorer], _ x: Int) -> Int {
  scorers.reduce(0) { $0 &+ $1.score(x) }
}

// MARK: class-bound protocol (AnyObject)

public protocol Pinger {
  func ping() -> Int
}

public protocol ClassPinger: AnyObject {
  func ping() -> Int
}

public final class PingTarget: Pinger, ClassPinger {
  public let id: Int
  public init(id: Int) { self.id = id }
  public func ping() -> Int { id }
}

@inline(never)
public func pingAll(_ targets: [any Pinger]) -> Int {
  targets.reduce(0) { $0 &+ $1.ping() }
}

@inline(never)
public func pingAllClassBound(_ targets: [any ClassPinger]) -> Int {
  targets.reduce(0) { $0 &+ $1.ping() }
}

// MARK: @objc dynamic vs Swift dispatch

public class LegacyCounter: NSObject {
  @objc dynamic public func step() -> Int { 1 }
}

public final class SwiftCounter {
  public init() {}
  public func step() -> Int { 1 }
}

@inline(never)
public func countLegacy(_ c: LegacyCounter, _ n: Int) -> Int {
  var total = 0
  for _ in 0..<n { total &+= c.step() }
  return total
}

@inline(never)
public func countSwift(_ c: SwiftCounter, _ n: Int) -> Int {
  var total = 0
  for _ in 0..<n { total &+= c.step() }
  return total
}

// MARK: cross-module: opaque function vs @inlinable

@inline(never)
public func scaleAllOpaque(_ xs: [Int]) -> Int {
  xs.reduce(0) { $0 &+ helperScale($1) }
}

@inline(never)
public func scaleAllInlinable(_ xs: [Int]) -> Int {
  xs.reduce(0) { $0 &+ helperScaleInlinable($1) }
}

@inline(never)
public func scaleAllMeters(_ xs: [Int]) -> Int {
  xs.reduce(0) { $0 &+ Meter($1).scaled }
}
