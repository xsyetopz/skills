// A separate module, so calls from Constructs cross a module boundary.

/// Not @inlinable: the body is only visible to clients when the compiler's
/// cross-module optimization serializes it (SwiftPM release builds pass
/// -enable-default-cmo); with library evolution it never is.
public func helperScale(_ x: Int) -> Int {
  x &* 3 &+ 1
}

/// @inlinable: the body is part of the module interface, so clients can
/// inline and specialize it even under -enable-library-evolution.
@inlinable
public func helperScaleInlinable(_ x: Int) -> Int {
  x &* 3 &+ 1
}

/// @usableFromInline lets an @inlinable body use an internal declaration.
/// @frozen fixes the layout under library evolution; without it the
/// struct is resilient, clients reach `raw` through an accessor, and a
/// root initializer cannot be @inlinable (SE-0193).
@frozen
public struct Meter {
  @usableFromInline var raw: Int

  @inlinable
  public init(_ raw: Int) { self.raw = raw }

  @inlinable
  public var scaled: Int { raw &* 3 &+ 1 }
}
