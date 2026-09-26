// Concurrency constructs: actors, Mutex, Atomic, OSAllocatedUnfairLock,
// batched actor calls, TaskGroup.
import Synchronization
import os

// MARK: actor (baseline for shared counters)

public actor CounterActor {
  var value = 0
  public init() {}
  public func increment() { value &+= 1 }
  public func add(_ n: Int) { value &+= n }
  public func read() -> Int { value }
}

// MARK: Mutex (Synchronization, macOS 15+)

public final class CounterMutex: Sendable {
  let state = Mutex(0)
  public init() {}
  public func increment() { state.withLock { $0 &+= 1 } }
  public func read() -> Int { state.withLock { $0 } }
}

// MARK: Atomic (Synchronization, macOS 15+)

public final class CounterAtomic: Sendable {
  let value = Atomic<Int>(0)
  public init() {}
  public func increment() {
    value.wrappingAdd(1, ordering: .relaxed)
  }
  public func read() -> Int { value.load(ordering: .relaxed) }
}

// MARK: OSAllocatedUnfairLock (os, macOS 13+)

public final class CounterUnfairLock: Sendable {
  let state = OSAllocatedUnfairLock(initialState: 0)
  public init() {}
  public func increment() { state.withLock { $0 &+= 1 } }
  public func read() -> Int { state.withLock { $0 } }
}

/// Runs `tasks` child tasks that each call the synchronous `body`
/// `perTask` times in a plain loop (how a lock or atomic is used).
public func hammerSync(
  tasks: Int, perTask: Int, _ body: @escaping @Sendable () -> Void
) async {
  await withTaskGroup(of: Void.self) { group in
    for _ in 0..<tasks {
      group.addTask {
        for _ in 0..<perTask { body() }
      }
    }
  }
}

/// Runs `tasks` child tasks that each await `body` `perTask` times.
public func hammer(
  tasks: Int, perTask: Int, _ body: @escaping @Sendable () async -> Void
) async {
  await withTaskGroup(of: Void.self) { group in
    for _ in 0..<tasks {
      group.addTask {
        for _ in 0..<perTask { await body() }
      }
    }
  }
}

// MARK: batch actor calls

@inline(never)
public func addOneByOne(_ counter: CounterActor, _ values: [Int]) async {
  for v in values { await counter.add(v) }
}

@inline(never)
public func addBatched(_ counter: CounterActor, _ values: [Int]) async {
  let sum = values.reduce(0, &+)
  await counter.add(sum)
}

// MARK: TaskGroup parallel map-reduce

@inline(never)
public func work(_ x: Int) -> Int {
  var h = x
  for _ in 0..<200 { h = (h &* 6_364_136_223_846_793_005) &+ 1 }
  return h & 0xFFFF
}

@inline(never)
public func checksumSequential(_ values: [Int]) -> Int {
  values.reduce(0) { $0 &+ work($1) }
}

@inline(never)
public func checksumTaskGroup(_ values: [Int], chunks: Int) async -> Int {
  let size = max(1, (values.count + chunks - 1) / chunks)
  return await withTaskGroup(of: Int.self) { group in
    for start in stride(from: 0, to: values.count, by: size) {
      let slice = values[start..<min(start + size, values.count)]
      group.addTask { slice.reduce(0) { $0 &+ work($1) } }
    }
    var total = 0
    for await partial in group { total &+= partial }
    return total
  }
}
