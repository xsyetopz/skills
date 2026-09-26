// Value, reference, and ownership constructs: struct vs class, copy-on-write,
// in-place mutation, consuming/borrowing, noncopyable types, exclusivity,
// captured variables.

// MARK: Structs instead of classes for plain data

public final class PointObject {
  public let x: Int
  public let y: Int
  public init(x: Int, y: Int) {
    self.x = x
    self.y = y
  }
}

public struct PointValue {
  public let x: Int
  public let y: Int
  public init(x: Int, y: Int) {
    self.x = x
    self.y = y
  }
}

@inline(never)
public func makeObjects(_ n: Int) -> [PointObject] {
  (0..<n).map { PointObject(x: $0, y: $0 &* 2) }
}

@inline(never)
public func makeValues(_ n: Int) -> [PointValue] {
  (0..<n).map { PointValue(x: $0, y: $0 &* 2) }
}

@inline(never)
public func sumObjects(_ points: [PointObject]) -> Int {
  points.reduce(0) { $0 &+ $1.x &+ $1.y }
}

@inline(never)
public func sumValues(_ points: [PointValue]) -> Int {
  points.reduce(0) { $0 &+ $1.x &+ $1.y }
}

// MARK: Linked traversal: ARC per hop

public final class ListNode {
  public let value: Int
  public let next: ListNode?
  public init(_ value: Int, _ next: ListNode?) {
    self.value = value
    self.next = next
  }
}

@inline(never)
public func sumList(_ head: ListNode?) -> Int {
  var total = 0
  var current = head
  while let node = current {
    total &+= node.value
    current = node.next
  }
  return total
}

@inline(never)
public func sumListValues(_ values: ContiguousArray<Int>) -> Int {
  var total = 0
  for v in values { total &+= v }
  return total
}

// MARK: Copy-on-write with isKnownUniquelyReferenced

final class Storage {
  var values: [Int]
  init(_ values: [Int]) { self.values = values }
}

/// Baseline: copies its storage on every mutation to keep value semantics.
public struct AlwaysCopyVector: Equatable {
  var storage: Storage
  public init(_ values: [Int]) { storage = Storage(values) }
  public var values: [Int] { storage.values }

  public mutating func set(_ index: Int, _ value: Int) {
    storage = Storage(storage.values)
    storage.values[index] = value
  }

  public static func == (a: Self, b: Self) -> Bool { a.values == b.values }
}

/// Candidate: copies only when the storage is shared.
public struct CowVector: Equatable {
  var storage: Storage
  public init(_ values: [Int]) { storage = Storage(values) }
  public var values: [Int] { storage.values }

  public mutating func set(_ index: Int, _ value: Int) {
    if !isKnownUniquelyReferenced(&storage) {
      storage = Storage(storage.values)
    }
    storage.values[index] = value
  }

  public static func == (a: Self, b: Self) -> Bool { a.values == b.values }
}

@inline(never)
public func fillAlwaysCopy(_ v: inout AlwaysCopyVector) {
  for i in 0..<v.values.count { v.set(i, i) }
}

@inline(never)
public func fillCow(_ v: inout CowVector) {
  for i in 0..<v.values.count { v.set(i, i) }
}

// MARK: inout instead of copy-and-reassign

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

// MARK: consuming parameter

@inline(never)
public func appendingOneConsuming(_ values: consuming [Int]) -> [Int] {
  values.append(1)
  return values
}

// MARK: borrowing parameter on an initializer

/// Initializer parameters are consumed by default (SE-0377): a caller that
/// keeps using its array must retain it for the call.
public struct Summary: Equatable {
  public let count: Int
  public let total: Int

  @inline(never)
  public init(consumingDefault items: [Int]) {
    count = items.count
    total = items.reduce(0, &+)
  }

  /// `borrowing` passes the array at +0; storing it would need `copy`.
  @inline(never)
  public init(borrowing items: borrowing [Int]) {
    count = items.count
    var sum = 0
    for i in items.indices { sum &+= items[i] }
    total = sum
  }
}

// MARK: Noncopyable (~Copyable) unique owner

/// Baseline: a class that owns a buffer. Two heap allocations (object and
/// buffer) and reference counting on every copy of the reference.
public final class SharedBuffer {
  public let base: UnsafeMutablePointer<Int>
  public let count: Int
  public init(count: Int) {
    self.count = count
    base = .allocate(capacity: count)
    base.initialize(repeating: 0, count: count)
  }
  deinit { base.deallocate() }
}

/// Candidate: a noncopyable struct that owns the same buffer. One heap
/// allocation, no reference count, deinit runs exactly once.
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
public func fillShared(_ buffer: SharedBuffer) -> Int {
  for i in 0..<buffer.count { buffer.base[i] = i }
  return (0..<buffer.count).reduce(0) { $0 &+ buffer.base[$1] }
}

@inline(never)
public func fillUnique(_ buffer: borrowing UniqueBuffer) -> Int {
  for i in 0..<buffer.count { buffer.base[i] = i }
  var total = 0
  for i in 0..<buffer.count { total &+= buffer.base[i] }
  return total
}

/// Factories return the owner, so the class instance escapes and must live
/// on the heap; a non-escaping instance is stack-promoted by -O.
@inline(never)
public func makeShared(_ n: Int) -> SharedBuffer {
  SharedBuffer(count: n)
}

@inline(never)
public func makeUnique(_ n: Int) -> UniqueBuffer {
  UniqueBuffer(count: n)
}

@inline(never)
public func sharedBufferRoundTrip(_ n: Int) -> Int {
  let buffer = makeShared(n)
  return fillShared(buffer)
}

@inline(never)
public func uniqueBufferRoundTrip(_ n: Int) -> Int {
  let buffer = makeUnique(n)
  return fillUnique(buffer)
}

// MARK: Exclusivity: class property in a loop vs a local accumulator

public final class Accumulator {
  public var total = 0
  public init() {}
}

/// An opaque call inside the loop: the optimizer cannot prove it does not
/// touch `acc.total`, so each iteration needs its own dynamic access check.
nonisolated(unsafe) public var progressHook: (Int) -> Void = { _ in }

@inline(never)
public func accumulateProperty(_ acc: Accumulator, _ values: [Int]) {
  for v in values {
    acc.total &+= v
    progressHook(v)
  }
}

@inline(never)
public func accumulateLocal(_ acc: Accumulator, _ values: [Int]) {
  var total = acc.total
  for v in values {
    total &+= v
    progressHook(v)
  }
  acc.total = total
}

// MARK: var captured by an escaping closure

@inline(never)
public func countWithEscapingCapture(_ values: [Int]) -> Int {
  var matches = 0
  let visit: (Int) -> Void = { if $0 > 0 { matches += 1 } }
  storeLastVisitor(visit)
  for v in values { visit(v) }
  return matches
}

@inline(never)
public func countWithInout(_ values: [Int]) -> Int {
  var matches = 0
  func visit(_ v: Int, _ count: inout Int) { if v > 0 { count += 1 } }
  for v in values { visit(v, &matches) }
  return matches
}

nonisolated(unsafe) var lastVisitor: ((Int) -> Void)?

@inline(never)
func storeLastVisitor(_ f: @escaping (Int) -> Void) {
  lastVisitor = f
}

// MARK: Wrapping arithmetic

@inline(never)
public func sumChecked(_ values: [Int]) -> Int {
  var total = 0
  for v in values { total += v }
  return total
}

@inline(never)
public func sumWrapping(_ values: [Int]) -> Int {
  var total = 0
  for v in values { total &+= v }
  return total
}
