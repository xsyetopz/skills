# Concurrency constructs

Cards for protecting shared state (actor, `Mutex`, `Atomic`,
`OSAllocatedUnfairLock`), reducing actor hops, and spreading CPU work with
`TaskGroup`. Pairs live in
`assets/examples/constructs/Sources/Constructs/Concurrency.swift`. The
oracle is the deterministic evidence: 8 child tasks x 1,000 increments
must end at exactly 8,000 for every counter type, and parallel results
must equal the sequential result.

Timings here are **not reliable**: they were taken while other agents
built on the same 10-core Apple M1 Max (load average 54 to 71), one run
per variant, Swift 6.3.3. They are a baseline for the next measurement,
not a ranking. The counter workload is 8 child tasks x 20,000
increments. The actor is awaited per increment (`hammer`); the three
synchronous primitives are called in a plain loop inside each child
task (`hammerSync`), as synchronous callers use them.

## Contents

- Actor-isolated state
- Mutex from Synchronization
- Atomic from Synchronization
- OSAllocatedUnfairLock
- Batching actor calls
- TaskGroup for CPU-bound work

## Actor-isolated state

**Definition.** An `actor` serializes access to its mutable state; calls
from outside are `await`ed and may suspend while another task runs on the
actor ([Concurrency][book-concurrency], [SE-0306][se306]).

**Use when.**

- The protected operation itself awaits (I/O, other actors), or state
  and the logic around it belong together and callers are already async.

**Do not use when.**

- Synchronous code must read or update the state: it cannot `await`.
  Use `Mutex` or `Atomic`.
- Each operation is tiny and frequent from many callers, and the
  profile shows actor hops or suspensions dominating: batch the calls
  (below) or use a lock.
- Correctness depends on no interleaving across an `await` inside an
  actor method: actors are re-entrant at suspension points.

**Example.** Runnable: `Concurrency.swift` (`CounterActor`).

```swift
public actor CounterActor {
    var value = 0
    public init() {}
    public func increment() { value &+= 1 }
    public func add(_ n: Int) { value &+= n }
    public func read() -> Int { value }
}
```

**Cost removed.** Data races, compared with unprotected state. This is
the baseline for the next three cards. Measured (three runs): 7.3, 9.7,
7.0 ms.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS actor counter` (8,000).
1. `sh assets/examples/verify.sh time counter`, repeated on an idle
   machine.

## Mutex from Synchronization

**Definition.** `Mutex<Value>` ([SE-0433][se433], Swift 6.0; the Swift
6.3.3 `Synchronization` interface marks it macOS 15, iOS 18) is a
noncopyable lock that owns its value; `withLock { }` gives
`inout` access. It wraps `os_unfair_lock` on Apple platforms, a futex on
Linux, and `SRWLOCK` on Windows; it is not recursive and does not
guarantee fairness.

**Use when.**

- Synchronous code on several threads updates small shared state, or a
  `Sendable` class needs mutable state without becoming an actor.

**Do not use when.**

- The critical section awaits or blocks for long: `withLock` cannot
  contain `await`, and blocked threads hold cooperative-pool workers.
- The lock is taken recursively (a `withLock` body calls code that
  locks again): the proposal leaves this platform-dependent (panic or
  deadlock).
- The deployment target is below macOS 15 / iOS 18: use
  `OSAllocatedUnfairLock` (macOS 13+).

**Example.** Runnable: `Concurrency.swift` (`CounterMutex`).

```swift
import Synchronization

public final class CounterMutex: Sendable {
    let state = Mutex(0)
    public init() {}
    public func increment() { state.withLock { $0 &+= 1 } }
    public func read() -> Int { state.withLock { $0 } }
}
```

**Cost removed.** Actor hops and suspensions for synchronous callers.
Measured (three runs, overloaded machine): 4.4, 4.2, 2.7 ms versus the
actor's 7.3, 9.7, 7.0 ms. Measure the real access pattern and
contention before switching.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS Mutex counter` (8,000).
1. `sh assets/examples/verify.sh time counter` on an idle machine.

## Atomic from Synchronization

**Definition.** `Atomic<Value>` ([SE-0410][se410], Swift 6.0; the Swift
6.3.3 `Synchronization` interface marks it macOS 15, iOS 18) provides
lock-free loads, stores, exchanges, compare-exchange, and
integer operations such as `wrappingAdd(_:ordering:)` with explicit
memory orderings (`.relaxed`, `.acquiring`, `.releasing`,
`.acquiringAndReleasing`, `.sequentiallyConsistent`). It must be stored
in a `let`; "declaring a `var` of `Atomic` type is now an error".

**Use when.**

- The shared state is one integer, boolean, or pointer updated
  independently (counters, flags, sequence numbers).

**Do not use when.**

- Two or more values must change together: separate atomics expose
  torn intermediate states. Use `Mutex`.
- `.relaxed` would publish other data: relaxed operations order nothing
  else, so readers can see the flag before the data. Use
  acquire/release pairs.

**Example.** Runnable: `Concurrency.swift` (`CounterAtomic`).

```swift
import Synchronization

public final class CounterAtomic: Sendable {
    let value = Atomic<Int>(0)
    public init() {}
    public func increment() {
        value.wrappingAdd(1, ordering: .relaxed)
    }
    public func read() -> Int { value.load(ordering: .relaxed) }
}
```

**Cost removed.** Lock acquisition for single-word updates. Measured
(three runs, overloaded machine): 0.36, 0.36, 0.95 ms, the fastest of
the four counters in every run.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS Atomic counter` (8,000).
1. Review every ordering argument: `.relaxed` is correct here only
   because the count publishes no other data.

## OSAllocatedUnfairLock

**Definition.** `OSAllocatedUnfairLock<State>` (os framework; the SDK
interface marks it macOS 13, iOS 16, tvOS 16, watchOS 9) is a
heap-allocated `os_unfair_lock` that can own state and is
`Sendable`; `withLock { }` gives `inout` access
([Apple documentation][unfair-doc]).

**Use when.**

- `Mutex` fits, but the deployment target is macOS 13-14 or
  iOS 16-17.

**Do not use when.**

- The code must build on Linux or Windows: the os framework is
  Apple-only. Use `Mutex` (Swift 6) there.
- The lock is taken recursively: like `Mutex` (whose Apple
  implementation is the same `os_unfair_lock`), it is not recursive.

**Example.** Runnable: `Concurrency.swift` (`CounterUnfairLock`).

```swift
import os

public final class CounterUnfairLock: Sendable {
    let state = OSAllocatedUnfairLock(initialState: 0)
    public init() {}
    public func increment() { state.withLock { $0 &+= 1 } }
    public func read() -> Int { state.withLock { $0 } }
}
```

**Cost removed.** Same as `Mutex`. Measured (three runs): 3.2, 5.6,
4.8 ms.

**Verify.**

1. `sh assets/examples/verify.sh verify`:
   `PASS OSAllocatedUnfairLock counter` (8,000).

## Batching actor calls

**Definition.** Each `await actor.method()` from outside the actor is a
potential hop and suspension. Computing locally and sending one combined
update replaces N hops with one.

**Use when.**

- A loop awaits an actor method per element, and the per-element
  updates commute (sums, counts, set insertions).

**Do not use when.**

- Other tasks must observe intermediate states in order (progress
  reporting, ordered logs).
- The per-element work needs actor state that changes between
  elements.

**Example.** Runnable: `Concurrency.swift` (`addBatched`).

```swift
@inline(never)
public func addBatched(_ counter: CounterActor, _ values: [Int]) async {
    let sum = values.reduce(0, &+)
    await counter.add(sum)
}
```

**Cost removed.** N - 1 actor calls. Measured, 100,000 values (three
runs): 15.7, 15.9, 43.1 ms -> 0.015, 0.016, 0.053 ms.

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS batched actor calls`
   (equal totals).
1. `sh assets/examples/verify.sh time batch`.

## TaskGroup for CPU-bound work

**Definition.** `withTaskGroup(of:)` runs child tasks concurrently on the
cooperative thread pool and collects results with `for await`; the
group waits for all children before returning ([SE-0304][se304],
[Concurrency][book-concurrency]).

**Use when.**

- A profile shows one core busy on independent, CPU-heavy items (each
  chunk takes at least tens of microseconds), and the combining step is
  associative.

**Do not use when.**

- Items are tiny: one child task per element costs more than the work.
  Chunk the input (the example uses 10 chunks).
- The combining operation is order-sensitive and not associative
  (floating-point sums change with grouping): results can differ from
  the sequential version.
- Children block threads (locks held long, synchronous I/O): the
  cooperative pool is shared by every task in the process.

**Example.** Runnable: `Concurrency.swift` (`checksumTaskGroup`).

```swift
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
```

**Cost removed.** Wall time on idle cores. Measured, 100,000 items (four
runs, overloaded machine): 17.6, 18.8, 18.0, 26.0 ms sequential ->
3.6, 15.6, 9.1, 16.7 ms with 10 chunks. CPU time does not drop.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal checksums for 1, 3, 8,
   and 20,000 chunks and for empty input.
1. `sh assets/examples/verify.sh time TaskGroup` on an idle machine;
   report cores and load.

[book-concurrency]: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/
[se306]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0306-actors.md
[se433]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0433-mutex.md
[se410]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0410-atomics.md
[unfair-doc]: https://developer.apple.com/documentation/os/osallocatedunfairlock
[se304]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md
