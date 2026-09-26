// Oracles: every pair returns the same result on edge inputs, then the
// counter named by the card moves in the claimed direction.
import CCount
import Constructs

func collectionChecks(_ n: Int) {
  for k in [0, 1, 2, 1000] {
    equal("reserveCapacity n=\(k)", squaresGrowing(k), squaresReserved(k))
  }
  fewerMallocs(
    "reserveCapacity", { squaresGrowing(n) },
    { squaresReserved(n) })

  let values = Array(0..<n)
  for input in [[], [1], [2, 3, 4], values] {
    equal(
      "reduce(into:) \(input.count)", evensByConcat(input),
      evensInto(input))
  }
  // Measured: -O already turns this `$0 + [$1]` into an in-place append.
  sameMallocs(
    "reduce(into:)", { evensByConcat(values) },
    { evensInto(values) })

  let particles = (0..<n).map { Particle(mass: $0) }
  let contiguous = ContiguousArray(particles)
  equal(
    "ContiguousArray", totalMass(particles),
    totalMassContiguous(contiguous))
  equal("ContiguousArray empty", totalMass([]), totalMassContiguous([]))

  for count in [0, 1, n] {
    equal(
      "withUnsafeBufferPointer count=\(count)",
      sumPrefixIndexed(values, count), sumPrefixUnsafe(values, count))
  }

  let bytes: [UInt8] = (0..<n).map { UInt8(truncatingIfNeeded: $0 &* 7) }
  for input in [[], [0, 255, 255], bytes] {
    var a = [Int](repeating: 0, count: 256)
    var b = a
    tallyChecked(&a, input)
    tallyUnsafe(&b, input)
    equal("withUnsafeMutableBufferPointer \(input.count)", a, b)
  }
  for input in [[], [255], bytes] {
    let slow = CallCounter()
    let fast = CallCounter()
    let a = checksumIterating(CountedBytes(input, slow))
    let b = checksumContiguous(CountedBytes(input, fast))
    equal("withContiguousStorageIfAvailable \(input.count)", a, b)
    print("CALLS next() \(input.count): \(slow.count) -> \(fast.count)")
    check(
      "withContiguousStorageIfAvailable skips next()",
      fast.count == 0, "\(fast.count) next() calls")
  }
  // Fallback path: a sequence without contiguous storage.
  let stride = Swift.stride(from: UInt8(0), to: 200, by: 3)
  equal(
    "withContiguousStorageIfAvailable fallback",
    checksumIterating(stride), checksumContiguous(stride))

  if #available(macOS 26.0, *) {
    for input in [[], [7], values] {
      equal("Span \(input.count)", sumArray(input), sumSpan(input.span))
    }
    let slice = values[3..<10]
    equal("Span from ArraySlice", slice.reduce(0, &+), sumSpan(slice.span))
    check("RawSpan little-endian host", 1.littleEndian == 1, "big-endian")
    for input in [
      [], [1, 2, 3], [1, 0, 0, 0, 255, 255, 255, 255, 9],
      bytes,
    ] {
      equal(
        "RawSpan \(input.count)", wordsShifting(input),
        wordsRawSpan(input.span.bytes))
    }
  } else {
    print("SKIP Span: needs the macOS 26 runtime for Array.span")
  }

  let keys = values.map { $0 &* 7919 }
  equal(
    "Dictionary(minimumCapacity:)", indexGrowing(keys),
    indexReserved(keys))
  equal(
    "Dictionary(minimumCapacity:) empty", indexGrowing([]),
    indexReserved([]))
  fewerMallocs(
    "Dictionary(minimumCapacity:)", { indexGrowing(keys) },
    { indexReserved(keys) })

  let hashA = CallCounter()
  let hashB = CallCounter()
  let words = (0..<n).map { $0 % 17 }
  let a = tallyLookupThenStore(words.map { CountedKey($0, hashA) })
  let b = tallyDefault(words.map { CountedKey($0, hashB) })
  equal(
    "subscript(_:default:)",
    a.map { [$0.key.value, $0.value] }.sorted { $0[0] < $1[0] },
    b.map { [$0.key.value, $0.value] }.sorted { $0[0] < $1[0] })
  print("HASH subscript(_:default:): \(hashA.count) -> \(hashB.count)")
  check(
    "subscript(_:default:) hashes", hashB.count < hashA.count,
    "\(hashB.count) >= \(hashA.count)")

  for input in [[], [1, 2], values] {
    equal(
      "lazy \(input.count)", firstLargeSquareEager(input, above: 50),
      firstLargeSquareLazy(input, above: 50))
  }
  fewerMallocs(
    "lazy", { firstLargeSquareEager(values, above: 50) },
    { firstLargeSquareLazy(values, above: 50) })

  sliceRetentionCheck()

  for input in [[], [5], values] {
    equal(
      "popFirst queue \(input.count)", drainRemoveFirst(input),
      drainHeadIndex(input))
  }
}

/// An ArraySlice keeps the whole base buffer alive; Array(slice) does not.
func sliceRetentionCheck() {
  let count = 1 << 20
  var kept: [ArraySlice<Int>] = []
  var copied: [[Int]] = []
  let start = ccount_bytes_in_use()
  do {
    let big = Array(repeating: 1, count: count)
    kept.append(headSlice(big))
  }
  let afterSlice = ccount_bytes_in_use()
  do {
    let big = Array(repeating: 1, count: count)
    copied.append(headCopy(big))
  }
  let afterCopy = ccount_bytes_in_use()
  equal("slice copy contents", Array(kept[0]), copied[0])
  // Slices keep the base's indices; Array(slice) is zero-based.
  let tail = Array(0..<4)[2...]
  check(
    "slice indices are not rebased",
    tail.startIndex == 2 && Array(tail).startIndex == 0,
    "startIndex \(tail.startIndex)")
  let retainedSlice = Int(afterSlice) - Int(start)
  let retainedCopy = Int(afterCopy) - Int(afterSlice)
  print("BYTES slice retention: \(retainedSlice) -> \(retainedCopy)")
  check(
    "slice retention", retainedCopy < retainedSlice / 100,
    "\(retainedCopy) vs \(retainedSlice)")
  blackHole(kept)
  blackHole(copied)
}

func valueChecks(_ n: Int) {
  let objects = makeObjects(n)
  let values = makeValues(n)
  equal("struct vs class", sumObjects(objects), sumValues(values))
  fewerMallocs(
    "struct vs class construction", { sumObjects(makeObjects(n)) },
    { sumValues(makeValues(n)) })

  var head: ListNode?
  for i in (0..<n).reversed() { head = ListNode(i, head) }
  let flat = Array(0..<n)
  let contiguous = ContiguousArray(flat)
  equal("linked list vs array", sumList(head), sumListValues(contiguous))
  fewerRetains(
    "linked list vs array", { sumList(head) },
    { sumListValues(contiguous) })

  // Copy-on-write: value semantics first, then allocation counts.
  let original = CowVector(Array(repeating: 0, count: 64))
  var copy = original
  copy.set(0, 99)
  check(
    "COW value semantics", original.values[0] == 0 && copy.values[0] == 99,
    "mutation leaked into the original")
  let seed = Array(repeating: 0, count: n)
  fewerMallocs(
    "isKnownUniquelyReferenced",
    {
      var v = AlwaysCopyVector(seed)
      fillAlwaysCopy(&v)
      return v.values
    },
    {
      var v = CowVector(seed)
      fillCow(&v)
      return v.values
    })

  fewerMallocs(
    "inout instead of reassign",
    {
      var a = [1, 2, 3]
      for _ in 0..<n { a = appendingOne(a) }
      return a
    },
    {
      var a = [1, 2, 3]
      for _ in 0..<n { appendOne(&a) }
      return a
    })
  fewerMallocs(
    "consuming parameter",
    {
      var a = [1, 2, 3]
      for _ in 0..<n { a = appendingOne(a) }
      return a
    },
    {
      var a = [1, 2, 3]
      for _ in 0..<n { a = appendingOneConsuming(a) }
      return a
    })
  // Measured: the last use of `a` is already moved into a consuming
  // parameter, so the explicit operator changes nothing here.
  sameMallocs(
    "consume operator",
    {
      var a = [1, 2, 3]
      for _ in 0..<n { a = appendingOneConsuming(a) }
      return a
    },
    {
      var a = [1, 2, 3]
      for _ in 0..<n { a = appendingOneConsuming(consume a) }
      return a
    })

  let source = Array(0..<n)
  fewerRetains(
    "borrowing init",
    {
      var out: [Summary] = []
      for _ in 0..<8 {
        out.append(Summary(consumingDefault: source))
      }
      return out
    },
    {
      var out: [Summary] = []
      for _ in 0..<8 { out.append(Summary(borrowing: source)) }
      return out
    })

  equal("~Copyable", sharedBufferRoundTrip(n), uniqueBufferRoundTrip(n))
  fewerMallocs(
    "~Copyable", { sharedBufferRoundTrip(n) },
    { uniqueBufferRoundTrip(n) })

  let accA = Accumulator()
  let accB = Accumulator()
  accumulateProperty(accA, flat)
  accumulateLocal(accB, flat)
  equal("exclusivity local accumulator", accA.total, accB.total)

  for input in [[], [-1, 0, 1], flat] {
    equal(
      "inout instead of captured var \(input.count)",
      countWithEscapingCapture(input), countWithInout(input))
  }
  fewerMallocs(
    "inout instead of captured var",
    { countWithEscapingCapture(flat) }, { countWithInout(flat) })

  equal("wrapping arithmetic", sumChecked(flat), sumWrapping(flat))
}

func dispatchChecks(_ n: Int) {
  let sides = Array(0..<n)
  equal(
    "final", totalAreaOpen(sides.map { Square(side: $0) }),
    totalAreaFinal(sides.map { FinalSquare(side: $0) }))
  equal("internal inferred final", tallyInternal(sides), sides.reduce(0, &+))
  equal("some vs any", callAny(sides), callSome(sides))
  equal(
    "generic stored property", pipelineAny(sides),
    pipelineGeneric(sides))
  equal(
    "some vs any Tripler", totalScoreAny(Tripler(), sides),
    totalScoreSome(Tripler(), sides))
  let mixed: [any Scorer] = [Doubler(), Tripler(), Doubler()]
  let known: [KnownScorer] = [
    .doubler(Doubler()), .tripler(Tripler()),
    .doubler(Doubler()),
  ]
  equal(
    "enum instead of [any P]", totalMixedAny(mixed, 7),
    totalMixedEnum(known, 7))
  let targets = (0..<n).map { PingTarget(id: $0) }
  equal("AnyObject protocol", pingAll(targets), pingAllClassBound(targets))
  let (_, rAny) = retains { pingAll(targets) }
  let (_, rClass) = retains { pingAllClassBound(targets) }
  print("RETAIN AnyObject protocol: \(rAny) -> \(rClass)")
  equal(
    "@objc dynamic", countLegacy(LegacyCounter(), n),
    countSwift(SwiftCounter(), n))
  equal("@inlinable", scaleAllOpaque(sides), scaleAllInlinable(sides))
  equal("@usableFromInline", scaleAllOpaque(sides), scaleAllMeters(sides))
}

func stringChecks(_ n: Int) {
  let cases = ["", ",", "a,b", "é,e\u{301},🙂", ",\u{301}x", "\r\n,"]
  for text in cases {
    let a = countCommasCharacters(text)
    let b = countCommasUTF8(text)
    // A combining mark after "," forms one Character that is not ",".
    if text == ",\u{301}x" {
      check(
        "utf8 view differs on \",\\u{301}\"", a == 0 && b == 1,
        "\(a) \(b)")
    } else {
      equal("utf8 view \(text.debugDescription)", a, b)
    }
  }
  let long = (0..<n).map { "field-number-\($0)-long" }.joined(separator: ",")
  equal(
    "Substring", fieldByteCountsCopying(long),
    fieldByteCountsSubstring(long))
  equal(
    "Substring empty", fieldByteCountsCopying(""),
    fieldByteCountsSubstring(""))
  fewerMallocs(
    "Substring (fields > 15 bytes)",
    { fieldByteCountsCopying(long) },
    { fieldByteCountsSubstring(long) })
  let short = (0..<n).map { "f\($0 % 10)" }.joined(separator: ",")
  // Only the intermediate [String] array differs: fields of up to 15
  // UTF-8 bytes are small strings stored inline.
  fewerMallocs(
    "Substring (small fields)", { fieldByteCountsCopying(short) },
    { fieldByteCountsSubstring(short) })

  let text = "e\u{301}👩‍💻🇪🇪" + String(repeating: "ab", count: 50)
  equal("offset indexing", charactersByOffset(text), charactersIterating(text))
  equal(
    "offset indexing empty", charactersByOffset(""),
    charactersIterating(""))

  let parts = (0..<n).map { "part\($0)" }
  equal("String.reserveCapacity", joinGrowing(parts), joinReserved(parts))
  fewerMallocs(
    "String.reserveCapacity", { joinGrowing(parts) },
    { joinReserved(parts) })

  let (_, small) = mallocs { makeString(repeating: "a", count: 15) }
  let (_, large) = mallocs { makeString(repeating: "a", count: 16) }
  print("ALLOC small string 15 -> 16 bytes: \(small) -> \(large)")
  check("small string", small == 0 && large == 1, "\(small) \(large)")
}

func concurrencyChecks() async {
  let tasks = 8
  let per = 1000
  let actor = CounterActor()
  await hammer(tasks: tasks, perTask: per) { await actor.increment() }
  let mutex = CounterMutex()
  await hammerSync(tasks: tasks, perTask: per) { mutex.increment() }
  let atomic = CounterAtomic()
  await hammerSync(tasks: tasks, perTask: per) { atomic.increment() }
  let unfair = CounterUnfairLock()
  await hammerSync(tasks: tasks, perTask: per) { unfair.increment() }
  let expected = tasks * per
  equal("actor counter", await actor.read(), expected)
  equal("Mutex counter", mutex.read(), expected)
  equal("Atomic counter", atomic.read(), expected)
  equal("OSAllocatedUnfairLock counter", unfair.read(), expected)

  let values = Array(1...1000)
  let one = CounterActor()
  let batched = CounterActor()
  await addOneByOne(one, values)
  await addBatched(batched, values)
  equal("batched actor calls", await one.read(), await batched.read())

  let input = Array(0..<10_000)
  for chunks in [1, 3, 8, 20_000] {
    equal(
      "TaskGroup chunks=\(chunks)", checksumSequential(input),
      await checksumTaskGroup(input, chunks: chunks))
  }
  equal(
    "TaskGroup empty", checksumSequential([]),
    await checksumTaskGroup([], chunks: 4))
}
