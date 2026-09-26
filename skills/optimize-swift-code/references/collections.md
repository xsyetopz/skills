# Collection constructs

Cards for `Array`, `ContiguousArray`, `Dictionary`, slices, unsafe
buffers, `Span`, and lazy sequences. Pairs live in
`assets/examples/constructs/Sources/Constructs/Collections.swift`. The
oracles in `Sources/Catalog/Checks.swift` check equal results on empty,
one-element, boundary, and 1,000-element inputs, then assert the counter
each card names. Counts are exact. Times are medians of 31 samples from
`sh assets/examples/verify.sh time` on a shared Apple M1 Max, Swift
6.3.3, `-O -wmo`; they are machine-specific and noisy.

## Contents

- Array reserveCapacity
- reduce(into:) instead of reduce with array concatenation
- ContiguousArray for class elements
- withUnsafeBufferPointer on a monotonic loop
- withUnsafeMutableBufferPointer for data-dependent indices
- withContiguousStorageIfAvailable fast path
- Span parameters
- RawSpan loads
- Dictionary minimumCapacity
- Dictionary subscript with default
- lazy sequences
- Copy a slice at an ownership boundary
- Queue with popFirst instead of removeFirst

## Array reserveCapacity

**Definition.** `reserveCapacity(n)` allocates storage for at least `n`
elements once, so later appends do not reallocate and copy
([Array.swift][array-src]).

**Use when.**

- The final count (or a tight upper bound) is known before a loop of
  `append` calls.

**Do not use when.**

- Called repeatedly with small increments (`count + 10` in a loop): the
  documentation warns this can make appends "linear" instead of
  amortized constant time. Let `append` grow the array.
- The bound is untrusted input (a length field from the network):
  clamp it first.

**Example.** Runnable: `Collections.swift` (`squaresReserved`).

```swift
@inline(never)
public func squaresReserved(_ n: Int) -> [Int] {
    var out: [Int] = []
    out.reserveCapacity(n)
    for i in 0..<n { out.append(i &* i) }
    return out
}
```

**Cost removed.** Growth reallocations. Measured: `ALLOC reserveCapacity:
10 -> 1` (n = 1,000; package-benchmark `Malloc (total)` p50 also
10 -> 1); n = 4,096: 4467.9 ns -> 3242.5 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal arrays for n = 0, 1, 2,
   1000 and the `ALLOC` line.
1. `BENCH_FILTER='reserveCapacity.*' sh assets/examples/verify.sh measure`.

## reduce(into:) instead of reduce with array concatenation

**Definition.** `reduce(_:_:)` passes the accumulator by value, so
`$0 + [$1]` can build a new array per element. `reduce(into:_:)` passes
it `inout` for in-place `append`.

**Use when.**

- The profile shows allocations proportional to the element count
  inside a `reduce` that builds a collection.

**Do not use when.**

- Expecting a gain without measuring. Measured: `-O` compiled
  `values.reduce([]) { $1.isMultiple(of: 2) ? $0 + [$1] : $0 }` to
  in-place appends, `ALLOC reduce(into:): 9 -> 9`. `reduce(into:)` is
  still clearer and does not depend on that optimization.

**Example.** Runnable: `Collections.swift` (`evensInto`).

```swift
@inline(never)
public func evensInto(_ values: [Int]) -> [Int] {
    values.reduce(into: []) {
        if $1.isMultiple(of: 2) { $0.append($1) }
    }
}
```

**Cost removed.** Per-element array allocation where the optimizer does
not rewrite the concatenation; 0 in the measured shape.

**Verify.**

1. `sh assets/examples/verify.sh verify` asserts equal results and equal
   counts (`no difference expected`).

## ContiguousArray for class elements

**Definition.** On Apple platforms, `Array<Element>` with a class or
`@objc` element may be backed by an `NSArray`, so element access carries
a bridging check; [`ContiguousArray`][contiguous-src] always stores
elements contiguously. For struct and enum elements the two "should
have similar efficiency" ([Optimization tips][tips]).

**Use when.**

- A hot loop iterates an array of class instances that is never bridged
  to Objective-C, and the assembly shows `_CocoaArrayWrapper` or
  `getElementSlowPath` calls.

**Do not use when.**

- The array goes to or comes from Objective-C APIs: bridging to and
  from `NSArray` then copies.
- Elements are structs or enums: no bridging path exists.

**Example.** Runnable: `Collections.swift` (`totalMassContiguous`).

```swift
@inline(never)
public func totalMassContiguous(
    _ particles: ContiguousArray<Particle>
) -> Int {
    var total = 0
    for p in particles { total &+= p.mass }
    return total
}
```

**Cost removed.** The bridged-storage branch: `totalMass` references
`_CocoaArrayWrapper`/`getElementSlowPath` (2 lines), the
`ContiguousArray` version none. Time for 4,096 elements: 2041.9 ns vs
2034.2 ns, no measurable difference.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS ContiguousArray`.
1. `sh assets/examples/verify.sh asm`: the slow-path expectations.

## withUnsafeBufferPointer on a monotonic loop

**Definition.** `withUnsafeBufferPointer { }` lends the array's storage
as an `UnsafeBufferPointer` for the closure's duration. Its subscript is
bounds-checked only in debug builds of client code ([SE-0447][se447]),
so a release build omits per-element checks.

**Use when.**

- Not for a plain `for i in 0..<count` loop without assembly evidence;
  see below.

**Do not use when.**

- The loop index grows monotonically to a bound: `-O` hoists the check
  (`count <= values.count` once) and vectorizes the loop. Measured:
  neither `sumPrefixIndexed` nor `sumPrefixUnsafe` has a check in its
  loop blocks; 336.7 ns vs 335.2 ns.
- The pointer would escape the closure, or the array is mutated inside
  it: undefined behavior.

**Example.** Runnable: `Collections.swift` (`sumPrefixUnsafe`).

```swift
precondition(count >= 0 && count <= values.count)
return values.withUnsafeBufferPointer { buffer in
    var total = 0
    for i in 0..<count { total &+= buffer[i] }
    return total
}
```

**Cost removed.** None measured in this shape.

**Verify.**

1. `sh assets/examples/verify.sh asm`: `sumPrefixIndexed` loop has no
   `b.ls`/`b.hi`/`brk`.

## withUnsafeMutableBufferPointer for data-dependent indices

**Definition.** When the index comes from data (`table[Int(byte)]`), the
compiler cannot hoist the bounds check, so each iteration compares and
branches. Borrowing the storage as an `UnsafeMutableBufferPointer` after
one explicit size check removes the per-element check, if every index is
proven in bounds.

**Use when.**

- The loop's assembly shows a compare-and-branch to a trap per
  iteration (`cmp` + `b.ls` in the loop blocks), and a one-time check
  proves every index valid (here: at least 256 slots and a `UInt8`
  index).

**Do not use when.**

- No proof exists that every index is in bounds: out-of-bounds writes
  corrupt memory silently.
- The table is created in the same function with a constant count.
  Measured: the compiler removed the check itself for a fresh local
  table built with `Array(repeating: 0, count: 256)`.

**Example.** Runnable: `Collections.swift` (`tallyUnsafe`).

```swift
@inline(never)
public func tallyUnsafe(_ table: inout [Int], _ bytes: [UInt8]) {
    precondition(table.count >= 256, "table needs 256 slots")
    table.withUnsafeMutableBufferPointer { slots in
        // PERF/SAFETY: slots.count >= 256 and Int(UInt8) is in
        // 0...255, so every index is in bounds. No escape.
        for b in bytes { slots[Int(b)] &+= 1 }
    }
}
```

**Cost removed.** One compare-and-branch per byte: loop-block matches of
`b.(ls|hs|lo|hi)` 1 -> 0. Time for 4,096 bytes: 1868.5 ns ->
1415.8 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal tables for empty,
   `[0, 255, 255]`, and 1,000 bytes.
1. `sh assets/examples/verify.sh asm`: `tallyChecked` loop some,
   `tallyUnsafe` loop none.

## withContiguousStorageIfAvailable fast path

**Definition.** `Sequence.withContiguousStorageIfAvailable(_:)`
([SE-0237][se237]) calls the closure with an `UnsafeBufferPointer` when
the sequence has contiguous storage and returns `nil` otherwise. A
generic function can take a buffer fast path and keep an iterator
fallback.

**Use when.**

- A generic `some Sequence<UInt8>` (or similar) API is hot and most
  callers pass arrays, `Data`, or UTF-8 views.

**Do not use when.**

- The function is not generic (it already takes `[T]` or `Span<T>`).
- There is no fallback path: sequences without contiguous storage
  (ranges, `stride`, lazy maps) return `nil`.

**Example.** Runnable: `Collections.swift` (`checksumContiguous`).

```swift
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
```

**Cost removed.** Iterator `next()` calls. Measured with a sequence that
counts them: `CALLS next() 1000: 1001 -> 0`.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal checksums for 0, 1, and
   1,000 bytes, plus the `stride` fallback.
1. The `CALLS next()` lines show 0 for the candidate.

## Span parameters

**Definition.** `Span<Element>` ([SE-0447][se447], Swift 6.2) is a
non-escapable, bounds-checked view of initialized contiguous memory.
`Array.span`, `ArraySlice.span`, `ContiguousArray.span`, and others
vend one ([SE-0456][se456]). Per the Swift 6.3.3 standard library
interface, `Span`, `ArraySlice.span`, and `ContiguousArray.span` are
available from macOS 10.14.4, while `Array.span` and
`String.UTF8View.span` require macOS 26 / iOS 26.
`subscript(unchecked:)` skips the check.

**Use when.**

- An API reads contiguous elements and should accept `Array`,
  `ArraySlice`, `ContiguousArray`, or `InlineArray` without being
  generic and without unsafe pointers.
- Replacing `withUnsafeBufferPointer` code: `Span` keeps bounds checks
  and cannot escape.

**Do not use when.**

- The deployment target is below macOS 26 / iOS 26 and callers pass
  `Array`: guard with `if #available(macOS 26.0, *)` or keep the
  existing API.
- Expecting speed over a plain array loop. Measured: neither `sumSpan`
  nor `sumArray` had loop bounds checks; 335.6 ns vs 336.9 ns.

**Example.** Runnable: `Collections.swift` (`sumSpan`).

```swift
@available(macOS 26.0, *)
@inline(never)
public func sumSpan(_ values: Span<Int>) -> Int {
    var total = 0
    for i in values.indices { total &+= values[i] }
    return total
}
// Callers: sumSpan(array.span), sumSpan(array[3..<10].span)
```

**Cost removed.** Unsafe-pointer code and generic entry points, at the
same machine cost as the array loop.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS Span ...` (skipped with a
   `SKIP Span` line below macOS 26).
1. `sh assets/examples/verify.sh asm`: `sumSpan` loop has no check.

## RawSpan loads

**Definition.** `RawSpan` is the untyped counterpart of `Span`
(`array.span.bytes`). `unsafeLoadUnaligned(fromByteOffset:as:)` reads a
`BitwiseCopyable` value at any byte offset after one bounds check for
the whole value; `fromUncheckedByteOffset:` skips it. The standard
library interface marks both `@unsafe`; the example marks the call with
an `unsafe` expression.

**Use when.**

- Parsing fixed-width fields (integers, floats) from a byte buffer
  where the baseline assembles them from individually checked bytes.

**Do not use when.**

- Byte order is not handled: the load uses host order; convert with
  `UInt32(littleEndian:)` (the oracle asserts a little-endian host).
- The type is not `BitwiseCopyable` (contains references).
- Deployment is below macOS 26 when the span comes from `Array`.

**Example.** Runnable: `Collections.swift` (`wordsRawSpan`).

```swift
while offset + 4 <= bytes.byteCount {
    let word = unsafe bytes.unsafeLoadUnaligned(
        fromByteOffset: offset, as: UInt32.self)
    out.append(UInt32(littleEndian: word))
    offset += 4
}
```

**Cost removed.** Bounds checks per byte. Measured assembly: 5 trap sites
in `wordsShifting` versus 2 in `wordsRawSpan` (recorded, not asserted);
4,096 bytes: 2419.4 ns vs 2319.0 ns, within noise.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal words for empty,
   3-byte, 9-byte (trailing byte ignored), and 1,000-byte inputs.
1. `sh assets/examples/verify.sh asm` prints both trap counts.

## Dictionary minimumCapacity

**Definition.** `Dictionary(minimumCapacity:)` and `reserveCapacity(_:)`
size the hash table once, so inserts do not trigger rehashing growth
([Dictionary.swift][dict-src]).

**Use when.**

- The number of distinct keys is known (building an index from an array
  of known size).

**Do not use when.**

- The key count is unknown or much smaller than the input (many
  duplicates): over-reserving wastes memory for the dictionary's
  lifetime.

**Example.** Runnable: `Collections.swift` (`indexReserved`).

```swift
@inline(never)
public func indexReserved(_ keys: [Int]) -> [Int: Int] {
    var index = [Int: Int](minimumCapacity: keys.count)
    for (offset, key) in keys.enumerated() { index[key] = offset }
    return index
}
```

**Cost removed.** Rehash allocations and re-insertions. Measured:
`ALLOC Dictionary(minimumCapacity:): 11 -> 1` (1,000 keys);
package-benchmark p50 30 µs -> 14 µs; 4,096 keys 151087.5 ns ->
61790.8 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal dictionaries (and empty).
1. `BENCH_FILTER='Dictionary.*' sh assets/examples/verify.sh measure`.

## Dictionary subscript with default

**Definition.** `dict[key, default: value]` returns the stored value or
the default, and as a mutating access it inserts when missing, all with
one hash lookup: `counts[key, default: 0] += 1`
([Dictionary.swift][dict-src]).

**Use when.**

- Code looks a key up and then stores it (`if let old = d[k] { d[k] =
  old + 1 } else { d[k] = 1 }`): two hash computations per update.

**Do not use when.**

- Absent keys must stay absent after a read: the mutating form inserts
  the default.

**Example.** Runnable: `Collections.swift` (`tallyDefault`).

```swift
@inline(never)
public func tallyDefault(_ keys: [CountedKey]) -> [CountedKey: Int] {
    var counts: [CountedKey: Int] = [:]
    for key in keys { counts[key, default: 0] += 1 }
    return counts
}
```

**Cost removed.** One hash computation per update. Measured with a key
type that counts `hash(into:)`: `HASH subscript(_:default:): 2026 ->
1027` for 1,000 updates of 17 keys (the remainder is growth rehashing).

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal counts and the `HASH`
   line.

## lazy sequences

**Definition.** `.lazy` returns a view whose `map`/`filter` closures run
only when elements are requested, without intermediate arrays; `first`
stops at the first match ([LazySequence.swift][lazy-src]).

**Use when.**

- A `map`/`filter` chain ends in `first`, `contains`, `prefix`, or one
  loop, and the intermediate arrays show in the allocation count.

**Do not use when.**

- The result is iterated more than once: closures run again on every
  pass, so side effects repeat and work doubles. Materialize with
  `Array()`.
- Closures have side effects whose count or order matters.

**Example.** Runnable: `Collections.swift` (`firstLargeSquareLazy`).

```swift
@inline(never)
public func firstLargeSquareLazy(_ values: [Int],
                                 above limit: Int) -> Int? {
    values.lazy.map { $0 &* $0 }.filter { $0 > limit }.first
}
```

**Cost removed.** Intermediate arrays and work past the first match.
Measured: `ALLOC lazy: 11 -> 0`; 4,096 elements with an early match
13825.4 ns -> 5.8 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal results for empty, no
   match, and 1,000 elements.

## Copy a slice at an ownership boundary

**Definition.** `ArraySlice` (and `Substring`) share the base buffer and
keep all of it alive; slice indices are not rebased to zero. `Array(slice)`
copies only the slice's elements ([Substring.swift][substring-src] warns
that long-lived substrings can "appear to be memory leakage").

**Use when.**

- A small slice of a large buffer is stored beyond the current scope
  (cached, returned from an API, put in a long-lived collection).
- Callers expect zero-based indices.

**Do not use when.**

- The slice is consumed in the same scope: the uncopied slice is
  cheaper there.

**Example.** Runnable: `Collections.swift` (`headSlice`, `headCopy`).

```swift
@inline(never)
public func headCopy(_ values: [Int]) -> [Int] {
    Array(values.prefix(4))
}
```

**Cost removed.** Retained memory. Measured with
`malloc_zone_statistics` `size_in_use` after the 8 MiB base array went
out of scope: `BYTES slice retention: 8405072 -> 112`.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal contents,
   `PASS slice indices are not rebased` (`Array(0..<4)[2...]` starts at
   index 2, its `Array` copy at 0), and the `BYTES` line.

## Queue with popFirst instead of removeFirst

**Definition.** `Array.removeFirst()` shifts every remaining element
(O(n)), so draining an array from the front is O(n²).
`ArraySlice.popFirst()` advances the slice's start index in O(1).

**Use when.**

- A loop drains an array from the front (`while !a.isEmpty {
  a.removeFirst() }`).

**Do not use when.**

- The queue also grows at the back for a long time: the slice keeps the
  consumed prefix alive. Use a ring buffer or `Deque` from
  swift-collections instead.

**Example.** Runnable: `Collections.swift` (`drainHeadIndex`).

```swift
var pending = values[...]
var checksum = 0
while let next = pending.popFirst() {
    checksum = checksum &* 31 &+ next
}
```

**Cost removed.** Element moves proportional to the remaining length.
Measured, 2,048 elements: 236831.3 ns -> 1931.3 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal checksums for empty,
   one, and 1,000 elements (order preserved).

[array-src]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/Array.swift
[contiguous-src]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/ContiguousArray.swift
[tips]: https://github.com/swiftlang/swift/blob/main/docs/OptimizationTips.rst
[se447]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0447-span-access-shared-contiguous-storage.md
[se456]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0456-stdlib-span-properties.md
[se237]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0237-contiguous-collection.md
[dict-src]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/Dictionary.swift
[lazy-src]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/LazySequence.swift
[substring-src]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/Substring.swift
