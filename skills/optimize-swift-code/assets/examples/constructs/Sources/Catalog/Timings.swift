// ContinuousClock timings: median ns per call, 31 samples. Machine-specific.
import Constructs
import Synchronization

func runTimings(filter: String) async {
  func want(_ name: String) -> Bool {
    filter.isEmpty || name.contains(filter)
  }
  let n = 4096
  let values = Array(0..<n)
  if want("reserveCapacity") {
    timePair(
      "reserveCapacity", calls: 200, { squaresGrowing(n).count },
      { squaresReserved(n).count })
  }
  if want("ContiguousArray") {
    let p = values.map { Particle(mass: $0) }
    let c = ContiguousArray(p)
    timePair(
      "ContiguousArray", calls: 200, { totalMass(p) },
      { totalMassContiguous(c) })
  }
  if want("withUnsafeBufferPointer") {
    timePair(
      "withUnsafeBufferPointer", calls: 200,
      { sumPrefixIndexed(values, n) },
      { sumPrefixUnsafe(values, n) })
  }
  if want("tally") {
    let bytes = values.map { UInt8(truncatingIfNeeded: $0 &* 7) }
    var ta = [Int](repeating: 0, count: 256)
    var tb = ta
    timePair(
      "withUnsafeMutableBufferPointer tally", calls: 200,
      {
        tallyChecked(&ta, bytes)
        return ta[0]
      },
      {
        tallyUnsafe(&tb, bytes)
        return tb[0]
      })
  }
  if want("RawSpan") {
    if #available(macOS 26.0, *) {
      let bytes = values.map { UInt8(truncatingIfNeeded: $0) }
      timePair(
        "RawSpan words", calls: 200,
        { wordsShifting(bytes).count },
        { wordsRawSpan(bytes.span.bytes).count })
    }
  }
  if want("Span") {
    if #available(macOS 26.0, *) {
      timePair(
        "Span", calls: 200, { sumArray(values) },
        { sumSpan(values.span) })
    }
  }
  if want("Dictionary") {
    let keys = values.map { $0 &* 7919 }
    timePair(
      "Dictionary(minimumCapacity:)", calls: 50,
      { indexGrowing(keys).count }, { indexReserved(keys).count })
  }
  if want("lazy") {
    timePair(
      "lazy", calls: 200,
      { firstLargeSquareEager(values, above: 50) ?? 0 },
      { firstLargeSquareLazy(values, above: 50) ?? 0 })
  }
  if want("popFirst") {
    let q = Array(values.prefix(2048))
    timePair(
      "popFirst queue", calls: 20, { drainRemoveFirst(q) },
      { drainHeadIndex(q) })
  }
  if want("struct") {
    let o = makeObjects(n)
    let v = makeValues(n)
    timePair(
      "struct vs class sum", calls: 200, { sumObjects(o) },
      { sumValues(v) })
  }
  if want("isKnownUniquelyReferenced") {
    let seed = Array(repeating: 0, count: 256)
    timePair(
      "isKnownUniquelyReferenced", calls: 50,
      {
        var v = AlwaysCopyVector(seed)
        fillAlwaysCopy(&v)
        return v.values.count
      },
      {
        var v = CowVector(seed)
        fillCow(&v)
        return v.values.count
      })
  }
  if want("~Copyable") {
    timePair(
      "~Copyable", calls: 200, { sharedBufferRoundTrip(64) },
      { uniqueBufferRoundTrip(64) })
  }
  if want("exclusivity") {
    let acc = Accumulator()
    timePair(
      "exclusivity", calls: 200,
      {
        accumulateProperty(acc, values)
        return acc.total
      },
      {
        accumulateLocal(acc, values)
        return acc.total
      })
  }
  if want("final") {
    let open = values.map { Square(side: $0) }
    let closed = values.map { FinalSquare(side: $0) }
    timePair(
      "final", calls: 200, { totalAreaOpen(open) },
      { totalAreaFinal(closed) })
  }
  if want("some") {
    timePair(
      "some vs any", calls: 200, { callAny(values) },
      { callSome(values) })
  }
  if want("objc") {
    let l = LegacyCounter()
    let s = SwiftCounter()
    timePair(
      "@objc dynamic", calls: 200, { countLegacy(l, n) },
      { countSwift(s, n) })
  }
  if want("inlinable") {
    timePair(
      "@inlinable", calls: 200, { scaleAllOpaque(values) },
      { scaleAllInlinable(values) })
  }
  if want("utf8") {
    let text = String(repeating: "abc,déf,", count: 512)
    timePair(
      "utf8 view", calls: 200, { countCommasCharacters(text) },
      { countCommasUTF8(text) })
  }
  if want("Substring") {
    let line = (0..<256).map { "field-number-\($0)-long" }
      .joined(separator: ",")
    timePair(
      "Substring", calls: 200,
      { fieldByteCountsCopying(line).count },
      { fieldByteCountsSubstring(line).count })
  }
  if want("offset") {
    let text = String(repeating: "ab", count: 256)
    timePair(
      "offset indexing", calls: 20,
      { charactersByOffset(text).count },
      { charactersIterating(text).count })
  }
  if want("counter") {
    await timeCounters()
  }
  if want("batch") {
    let clock = ContinuousClock()
    let input = Array(0..<100_000)
    let one = CounterActor()
    let batched = CounterActor()
    let a = await clock.measure { await addOneByOne(one, input) }
    let b = await clock.measure { await addBatched(batched, input) }
    let r1 = await one.read()
    let r2 = await batched.read()
    precondition(r1 == r2)
    print("TIME batched actor calls (one run each): \(a) -> \(b)")
  }
  if want("TaskGroup") {
    let input = Array(0..<100_000)
    let clock = ContinuousClock()
    var seq = 0
    let a = clock.measure { seq = checksumSequential(input) }
    var par = 0
    let b = await clock.measure {
      par = await checksumTaskGroup(input, chunks: 10)
    }
    precondition(seq == par)
    print("TIME TaskGroup (one run each): \(a) -> \(b)")
  }
}

/// Wall time for 8 tasks x 20,000 increments per counter type.
func timeCounters() async {
  let clock = ContinuousClock()
  let actor = CounterActor()
  let mutex = CounterMutex()
  let atomic = CounterAtomic()
  let unfair = CounterUnfairLock()
  let tActor = await clock.measure {
    await hammer(tasks: 8, perTask: 20_000) { await actor.increment() }
  }
  let tMutex = await clock.measure {
    await hammerSync(tasks: 8, perTask: 20_000) {
      mutex.increment()
    }
  }
  let tAtomic = await clock.measure {
    await hammerSync(tasks: 8, perTask: 20_000) {
      atomic.increment()
    }
  }
  let tUnfair = await clock.measure {
    await hammerSync(tasks: 8, perTask: 20_000) {
      unfair.increment()
    }
  }
  precondition(mutex.read() == atomic.read())
  print(
    "TIME counters actor=\(tActor) Mutex=\(tMutex) "
      + "Atomic=\(tAtomic) OSAllocatedUnfairLock=\(tUnfair)")
}
