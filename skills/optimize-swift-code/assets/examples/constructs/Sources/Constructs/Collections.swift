// Collection constructs: capacity, storage choice, unsafe and span access,
// dictionary updates, laziness, slices. Baseline and candidate compute the
// same result; Catalog/Checks.swift holds the oracles.

// MARK: Array.reserveCapacity

@inline(never)
public func squaresGrowing(_ n: Int) -> [Int] {
  var out: [Int] = []
  for i in 0..<n { out.append(i &* i) }
  return out
}

@inline(never)
public func squaresReserved(_ n: Int) -> [Int] {
  var out: [Int] = []
  out.reserveCapacity(n)
  for i in 0..<n { out.append(i &* i) }
  return out
}

// MARK: reduce(into:) instead of reduce with +

@inline(never)
public func evensByConcat(_ values: [Int]) -> [Int] {
  values.reduce([]) { $1.isMultiple(of: 2) ? $0 + [$1] : $0 }
}

@inline(never)
public func evensInto(_ values: [Int]) -> [Int] {
  values.reduce(into: []) { if $1.isMultiple(of: 2) { $0.append($1) } }
}

// MARK: ContiguousArray for class elements

public final class Particle {
  public let mass: Int
  public init(mass: Int) { self.mass = mass }
}

@inline(never)
public func totalMass(_ particles: [Particle]) -> Int {
  var total = 0
  for p in particles { total &+= p.mass }
  return total
}

@inline(never)
public func totalMassContiguous(_ particles: ContiguousArray<Particle>) -> Int {
  var total = 0
  for p in particles { total &+= p.mass }
  return total
}

// MARK: withUnsafeBufferPointer

/// Monotonic loop: -O hoists the bounds check out of the loop, so the
/// unsafe candidate below changes nothing (measured; see the card).
@inline(never)
public func sumPrefixIndexed(_ values: [Int], _ count: Int) -> Int {
  var total = 0
  for i in 0..<count { total &+= values[i] }
  return total
}

@inline(never)
public func sumPrefixUnsafe(_ values: [Int], _ count: Int) -> Int {
  // PERF/SAFETY: count <= values.count is checked once here; the buffer
  // pointer does not escape the closure and the array is not mutated
  // while it is borrowed.
  precondition(count >= 0 && count <= values.count, "count out of range")
  return values.withUnsafeBufferPointer { buffer in
    var total = 0
    for i in 0..<count { total &+= buffer[i] }
    return total
  }
}

/// Data-dependent index into a caller's table of unknown size: one bounds
/// check per byte stays in the loop.
@inline(never)
public func tallyChecked(_ table: inout [Int], _ bytes: [UInt8]) {
  for b in bytes { table[Int(b)] &+= 1 }
}

@inline(never)
public func tallyUnsafe(_ table: inout [Int], _ bytes: [UInt8]) {
  precondition(table.count >= 256, "table needs 256 slots")
  table.withUnsafeMutableBufferPointer { slots in
    // PERF/SAFETY: slots.count >= 256 (checked above) and Int(UInt8)
    // is in 0...255, so every index is in bounds. `slots` does not
    // escape the closure.
    for b in bytes { slots[Int(b)] &+= 1 }
  }
}

// MARK: withContiguousStorageIfAvailable

@inline(never)
public func checksumIterating<S: Sequence>(_ bytes: S) -> Int
where S.Element == UInt8 {
  var sum = 0
  for b in bytes { sum = (sum &* 31) &+ Int(b) }
  return sum
}

@inline(never)
public func checksumContiguous<S: Sequence>(_ bytes: S) -> Int
where S.Element == UInt8 {
  let fast = bytes.withContiguousStorageIfAvailable { buffer in
    var sum = 0
    for b in buffer { sum = (sum &* 31) &+ Int(b) }
    return sum
  }
  if let fast { return fast }
  var sum = 0
  for b in bytes { sum = (sum &* 31) &+ Int(b) }
  return sum
}

/// A sequence that counts `next()` calls and forwards contiguous storage,
/// so the oracle can prove which path ran.
public struct CountedBytes: Sequence {
  public let storage: [UInt8]
  public let calls: CallCounter

  public init(_ storage: [UInt8], _ calls: CallCounter) {
    self.storage = storage
    self.calls = calls
  }

  public struct Iterator: IteratorProtocol {
    var inner: IndexingIterator<[UInt8]>
    let calls: CallCounter
    public mutating func next() -> UInt8? {
      calls.count += 1
      return inner.next()
    }
  }

  public func makeIterator() -> Iterator {
    Iterator(inner: storage.makeIterator(), calls: calls)
  }

  public func withContiguousStorageIfAvailable<R>(
    _ body: (UnsafeBufferPointer<UInt8>) throws -> R
  ) rethrows -> R? {
    try storage.withUnsafeBufferPointer(body)
  }
}

public final class CallCounter {
  public var count = 0
  public init() {}
}

// MARK: Span (SE-0447, Swift 6.2; Array.span needs the macOS 26 runtime)

@available(macOS 26.0, *)
@inline(never)
public func sumSpan(_ values: Span<Int>) -> Int {
  var total = 0
  for i in values.indices { total &+= values[i] }
  return total
}

@inline(never)
public func sumArray(_ values: [Int]) -> Int {
  var total = 0
  for i in values.indices { total &+= values[i] }
  return total
}

// MARK: RawSpan loads instead of byte shifting

/// Little-endian UInt32 words, assembled from four checked byte reads.
@inline(never)
public func wordsShifting(_ bytes: [UInt8]) -> [UInt32] {
  var out: [UInt32] = []
  out.reserveCapacity(bytes.count / 4)
  var i = 0
  while i + 4 <= bytes.count {
    out.append(
      UInt32(bytes[i]) | UInt32(bytes[i + 1]) << 8
        | UInt32(bytes[i + 2]) << 16 | UInt32(bytes[i + 3]) << 24)
    i += 4
  }
  return out
}

@available(macOS 26.0, *)
@inline(never)
public func wordsRawSpan(_ bytes: RawSpan) -> [UInt32] {
  var out: [UInt32] = []
  out.reserveCapacity(bytes.byteCount / 4)
  var offset = 0
  while offset + 4 <= bytes.byteCount {
    // Checked load: traps if the 4 bytes are not inside the span.
    // Host byte order; the oracle asserts a little-endian host.
    let word = unsafe bytes.unsafeLoadUnaligned(
      fromByteOffset: offset, as: UInt32.self)
    out.append(UInt32(littleEndian: word))
    offset += 4
  }
  return out
}

// MARK: Dictionary(minimumCapacity:) / reserveCapacity

@inline(never)
public func indexGrowing(_ keys: [Int]) -> [Int: Int] {
  var index: [Int: Int] = [:]
  for (offset, key) in keys.enumerated() { index[key] = offset }
  return index
}

@inline(never)
public func indexReserved(_ keys: [Int]) -> [Int: Int] {
  var index = [Int: Int](minimumCapacity: keys.count)
  for (offset, key) in keys.enumerated() { index[key] = offset }
  return index
}

// MARK: Dictionary subscript(_:default:)

/// A key that counts hash(into:) calls, so the oracle can count lookups.
public struct CountedKey: Hashable {
  public let value: Int
  public let hashes: CallCounter

  public init(_ value: Int, _ hashes: CallCounter) {
    self.value = value
    self.hashes = hashes
  }

  public static func == (a: CountedKey, b: CountedKey) -> Bool {
    a.value == b.value
  }

  public func hash(into hasher: inout Hasher) {
    hashes.count += 1
    hasher.combine(value)
  }
}

@inline(never)
public func tallyLookupThenStore(_ keys: [CountedKey]) -> [CountedKey: Int] {
  var counts: [CountedKey: Int] = [:]
  for key in keys {
    if let old = counts[key] {
      counts[key] = old + 1
    } else {
      counts[key] = 1
    }
  }
  return counts
}

@inline(never)
public func tallyDefault(_ keys: [CountedKey]) -> [CountedKey: Int] {
  var counts: [CountedKey: Int] = [:]
  for key in keys { counts[key, default: 0] += 1 }
  return counts
}

// MARK: lazy

@inline(never)
public func firstLargeSquareEager(_ values: [Int], above limit: Int) -> Int? {
  values.map { $0 &* $0 }.filter { $0 > limit }.first
}

@inline(never)
public func firstLargeSquareLazy(_ values: [Int], above limit: Int) -> Int? {
  values.lazy.map { $0 &* $0 }.filter { $0 > limit }.first
}

// MARK: Copy a slice at an ownership boundary

@inline(never)
public func headSlice(_ values: [Int]) -> ArraySlice<Int> {
  values.prefix(4)
}

@inline(never)
public func headCopy(_ values: [Int]) -> [Int] {
  Array(values.prefix(4))
}

// MARK: Queue without removeFirst

@inline(never)
public func drainRemoveFirst(_ values: [Int]) -> Int {
  var pending = values
  var checksum = 0
  while !pending.isEmpty {
    checksum = checksum &* 31 &+ pending.removeFirst()
  }
  return checksum
}

@inline(never)
public func drainHeadIndex(_ values: [Int]) -> Int {
  var pending = values[...]
  var checksum = 0
  while let next = pending.popFirst() {
    checksum = checksum &* 31 &+ next
  }
  return checksum
}
