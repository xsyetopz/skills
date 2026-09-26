// Baseline/candidate pairs measured with package-benchmark. Inputs are
// built outside the measured loop; blackHole keeps every result alive.
import Benchmark
import Constructs

let benchmarks: @Sendable () -> Void = {
  Benchmark.defaultConfiguration.metrics = [
    .wallClock, .mallocCountTotal, .retainCount, .releaseCount,
  ]
  Benchmark.defaultConfiguration.maxDuration = .seconds(1)

  let n = 1000
  Benchmark("reserveCapacity/baseline") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(squaresGrowing(n))
    }
  }
  Benchmark("reserveCapacity/candidate") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(squaresReserved(n))
    }
  }

  let keys = (0..<n).map { $0 &* 7919 }
  Benchmark("Dictionary(minimumCapacity:)/baseline") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(indexGrowing(keys))
    }
  }
  Benchmark("Dictionary(minimumCapacity:)/candidate") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(indexReserved(keys))
    }
  }

  let line = (0..<256).map { "field-number-\($0)-long" }
    .joined(separator: ",")
  Benchmark("Substring/baseline") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(fieldByteCountsCopying(line))
    }
  }
  Benchmark("Substring/candidate") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(fieldByteCountsSubstring(line))
    }
  }

  var head: ListNode?
  for i in (0..<n).reversed() { head = ListNode(i, head) }
  let flat = ContiguousArray(0..<n)
  Benchmark("linked list vs array/baseline") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(sumList(head))
    }
  }
  Benchmark("linked list vs array/candidate") { benchmark in
    for _ in benchmark.scaledIterations {
      blackHole(sumListValues(flat))
    }
  }
}
