// Equivalence, allocation, ARC, and timing helpers for the catalog.
import CCount

nonisolated(unsafe) var failures = 0
nonisolated(unsafe) var sink = 0

/// Keeps a value alive and observable so the optimizer cannot drop the work.
@inline(never)
func blackHole<T>(_ value: T) {
  withUnsafePointer(to: value) { sink &+= Int(bitPattern: $0) & 1 }
}

func check(_ name: String, _ ok: Bool, _ detail: @autoclosure () -> String) {
  if ok {
    print("PASS \(name)")
  } else {
    failures += 1
    print("FAIL \(name): \(detail())")
  }
}

func equal<T: Equatable>(_ name: String, _ a: T, _ b: T) {
  check(name, a == b, "\(a) != \(b)")
}

/// Runs `body` once to warm up (lazy metadata, first-call caches), then
/// returns the result and the malloc calls of the second run.
@inline(never)
func mallocs<T>(_ body: () -> T) -> (T, UInt64) {
  blackHole(body())
  let before = ccount_mallocs()
  let result = body()
  return (result, ccount_mallocs() - before)
}

@inline(never)
func retains<T>(_ body: () -> T) -> (T, UInt64) {
  blackHole(body())
  let before = ccount_retains()
  let result = body()
  return (result, ccount_retains() - before)
}

/// Equal results, and the candidate makes strictly fewer malloc calls.
func fewerMallocs<T: Equatable>(
  _ name: String, _ baseline: () -> T, _ candidate: () -> T
) {
  let (a, na) = mallocs(baseline)
  let (b, nb) = mallocs(candidate)
  print("ALLOC \(name): \(na) -> \(nb)")
  equal("\(name) result", a, b)
  check("\(name) allocations", nb < na, "\(nb) >= \(na)")
}

/// Equal results, and the candidate makes strictly fewer retains.
func fewerRetains<T: Equatable>(
  _ name: String, _ baseline: () -> T, _ candidate: () -> T
) {
  let (a, na) = retains(baseline)
  let (b, nb) = retains(candidate)
  print("RETAIN \(name): \(na) -> \(nb)")
  equal("\(name) result", a, b)
  check("\(name) retains", nb < na, "\(nb) >= \(na)")
}

/// Equal results and the same malloc count: records a "no difference".
func sameMallocs<T: Equatable>(
  _ name: String, _ baseline: () -> T, _ candidate: () -> T
) {
  let (a, na) = mallocs(baseline)
  let (b, nb) = mallocs(candidate)
  print("ALLOC \(name): \(na) -> \(nb) (no difference expected)")
  equal("\(name) result", a, b)
  check("\(name) allocations", nb == na, "\(nb) != \(na)")
}

/// Median nanoseconds per call over `samples` samples of `calls` calls,
/// measured with ContinuousClock.
func medianNanos(samples: Int = 31, calls: Int, _ body: () -> Int) -> Double {
  for _ in 0..<calls { blackHole(body()) }
  let clock = ContinuousClock()
  var results: [Double] = []
  results.reserveCapacity(samples)
  for _ in 0..<samples {
    let elapsed = clock.measure {
      for _ in 0..<calls { blackHole(body()) }
    }
    let c = elapsed.components
    let ns = Double(c.seconds) * 1e9 + Double(c.attoseconds) / 1e9
    results.append(ns / Double(calls))
  }
  results.sort()
  return results[results.count / 2]
}

func timePair(
  _ name: String, calls: Int, _ baseline: () -> Int, _ candidate: () -> Int
) {
  let a = medianNanos(calls: calls, baseline)
  let b = medianNanos(calls: calls, candidate)
  let fa = String(Int((a * 10).rounded())).insertingDecimal()
  let fb = String(Int((b * 10).rounded())).insertingDecimal()
  print("TIME \(name): \(fa) ns -> \(fb) ns (median of 31)")
}

extension String {
  /// "12345" -> "1234.5" without Foundation formatting.
  func insertingDecimal() -> String {
    let padded =
      count < 2
      ? String(repeating: "0", count: 2 - count) + self
      : self
    return "\(padded.dropLast()).\(padded.suffix(1))"
  }
}
