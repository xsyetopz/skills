# Coroutines

kotlinx.coroutines 1.11.0 on the JVM: dispatchers, structured
concurrency, blocking bridges, Flow operators, locks, channels, and
cancellation. Pairs live in
[`Coroutines.kt`][Coroutines.kt].
Timing claims use `runTest` virtual time, which is exact (see
[measurement](measurement.md#virtual-time-with-runtest)). Dispatcher
claims use latches, so peaks are exact. `verify.sh verify coroutines`
runs all of them. Results come from the machine in the measurement
reference (10 cores).

Tier: Executed. `verify coroutines`, `benchmark`, and `measure` ran
locally for every card in this file.

## Contents

- Dispatchers.IO for blocking calls
- limitedParallelism for a bounded resource
- Structured concurrency instead of GlobalScope
- async and awaitAll for independent calls
- Suspend calls instead of runBlocking in hot paths
- Flow buffer
- Flow conflate
- flowOn for upstream context
- Mutex for critical sections that suspend
- Atomics or synchronized for critical sections that do not suspend
- Channel capacity
- Rethrow CancellationException
- ensureActive in CPU-bound loops

## Dispatchers.IO for blocking calls

**Definition.** `Dispatchers.Default` uses at most as many threads as
CPU cores, "but is at least two" ([Dispatchers.Default][default]).
`Dispatchers.IO` is for blocking I/O. Its limit is 64 threads or the
number of cores, whichever is larger (property
`kotlinx.coroutines.io.parallelism`). It shares threads with `Default`,
so `withContext(Dispatchers.IO)` from `Default` often does not switch
threads ([Dispatchers.IO][io]).

**Use when.**

- A coroutine calls a blocking API (JDBC, `File` reads, `Thread.sleep`,
  a latch), and the profile or thread dump shows
  `DefaultDispatcher-worker` threads parked in it while CPU work waits.

**Do not use when.**

- The call already suspends (Ktor, R2DBC, `delay`): moving it adds a
  dispatch and no capacity.
- The blocking resource has its own limit (a pool of 10 connections):
  64 threads just queue on it. Use the next card.

**Example.**

```kotlin
suspend fun loadRow(id: Int): Row =
    withContext(Dispatchers.IO) { jdbcLoad(id) } // blocking call
```

Runnable: `peakBlocking(Dispatchers.Default, 32)` against
`peakBlocking(Dispatchers.IO, 32, waitMillis = 5_000)`. Each task blocks
on a latch until all 32 arrive or the wait passes (100 ms on `Default`,
5 s on `IO`).

**Cost removed.** Blocked CPU threads. Measured: at most 10 tasks blocked
at once on `Default` (10 cores; the rest waited for a thread), and all 32
at once on `IO`.

**Verify.**

1. `verify.sh verify coroutines`: `PASS dispatcher default blocks`
   (peak <= cores) and `PASS dispatcher io peak` (32).
1. In the target: a thread dump (`jcmd <pid> Thread.print`) under load
   shows no `DefaultDispatcher-worker` blocked in I/O frames.

## limitedParallelism for a bounded resource

**Definition.** `dispatcher.limitedParallelism(n, name = null)` returns a
view that runs at most `n` coroutines at once on the original
dispatcher's threads. Views of `Dispatchers.IO` are elastic and not
bounded by its 64-thread limit ([limitedParallelism][limited]).

**Use when.**

- A blocking resource has a fixed capacity (connection pool, rate-limited
  client, a native library that allows `n` callers). It replaces
  `newFixedThreadPoolContext(n)` without dedicated threads.
- A component must be confined to one thread at a time
  (`limitedParallelism(1)`).

**Do not use when.**

- The work must stay on one specific thread (UI, thread-local native
  state): a view "does not guarantee" the same threads.
- The limit is meant to protect CPU: `Default` is already sized to the
  cores.

**Example.**

```kotlin
val db = Dispatchers.IO.limitedParallelism(4)

suspend fun query(id: Int): Row = withContext(db) { jdbcLoad(id) }
```

**Cost removed.** Oversubscription of the resource. Measured: 16
blocking tasks on `Dispatchers.IO.limitedParallelism(4)` peak at
exactly 4.

**Verify.**

1. `verify.sh verify coroutines`: `PASS limitedParallelism peak`.
1. `limitedParallelism` needs no opt-in in 1.11.0: a one-line file using
   it compiled with `kotlinc -Werror` and no `@OptIn` (checked locally).

## Structured concurrency instead of GlobalScope

**Definition.** A coroutine launched in a scope is a child of that
scope's `Job`: the parent waits for it and cancels it when the parent is
cancelled ([coroutine basics][basics]). `GlobalScope` has no `Job`, so
"it is impossible to cancel all coroutines launched in it". It is a
`@DelicateCoroutinesApi` ([GlobalScope][global]).

**Use when.**

- A request, component, or screen starts work that its lifetime should
  bound: launch it in that scope, or in `coroutineScope { }`.

**Do not use when.**

- The work must outlive every caller (an application-lifetime reporter).
  Even then, prefer an application scope you can cancel on shutdown.

**Example.**

```kotlin
suspend fun refresh(ids: List<Int>) = coroutineScope {
    for (id in ids) launch { update(id) } // children of this scope
} // returns after every child completes; cancellation reaches all
```

Runnable: `childOutlivesCancelledParent(structured)`.

**Cost removed.** Work that leaks past cancellation (CPU, sockets,
memory). Oracle: the `GlobalScope` child still finished after its parent
was cancelled; the structured child was cancelled.

**Verify.**

1. `verify.sh verify coroutines`: `PASS globalscope leak` (true) and
   `PASS structured cancel` (false).
1. In the target: `rg -n 'GlobalScope' src/` has no hits on request
   paths.

## async and awaitAll for independent calls

**Definition.** `async { }` starts a child coroutine and returns a
`Deferred`. `awaitAll()` suspends until all complete and fails when any
fails. Inside `coroutineScope`, independent suspending calls then overlap
instead of running in sequence ([composing suspending
functions][compose]).

**Use when.**

- A function awaits several independent suspending calls in sequence
  (remote fetches, file reads), so total latency is their sum.

**Do not use when.**

- The calls depend on each other's results or must run in order.
- n is unbounded: thousands of concurrent requests overload the callee.
  Bound them with `limitedParallelism` or a `Semaphore`.

**Example.**

```kotlin
suspend fun pricesConcurrent(ids: List<Int>): List<Int> = coroutineScope {
    ids.map { async { fetchPrice(it) } }.awaitAll()
}
```

**Cost removed.** Serial waiting. Virtual time for three 100 ms fetches:
sequential 300 ms, concurrent 100 ms, with results in the same order.

**Verify.**

1. `verify.sh verify coroutines`: `async awaitAll result`,
   `async virtual time sequential` (300), and `... concurrent` (100).

## Suspend calls instead of runBlocking in hot paths

**Definition.** `runBlocking` starts an event loop and blocks the
calling thread until its coroutine finishes. It is meant for `main`,
tests, and non-suspend callbacks. "Calling runBlocking from a suspend
function is redundant", and it blocks the thread instead of releasing
it, "potentially leading to thread starvation" ([runBlocking][runblocking]).

**Use when.**

- A profile or allocation trace shows `BlockingCoroutine` or
  `BlockingEventLoop` per request or per item, or `runBlocking` appears
  inside suspend functions or on dispatcher threads.

**Do not use when.**

- It is the single bridge at a program entry point or a blocking API
  boundary (servlet, JUnit test): one `runBlocking` there is correct.

**Example.**

```kotlin
fun squaresSuspendCandidate(n: Int): Int = runBlocking {
    var sum = 0
    repeat(n) { sum += square(it) } // suspend calls, one bridge
    sum
}
```

Runnable: `squaresRunBlockingBaseline` (one `runBlocking` per item) and
`squaresSuspendCandidate`.

**Cost removed.** 99 of 100 event loops. Measured (100 items): baseline
24,800 B/call, candidate 1,912 B/call. JMH: `runBlockingBaseline`
7,467 ± 642.3 ns/op, 24,800 B/op; `runBlockingCandidate`
218.7 ± 10.8 ns/op, 312 B/op.

**Verify.**

1. `verify.sh verify coroutines`: `PASS runBlocking result`,
   `PASS alloc runBlocking per call`.
1. In the target: `rg -n 'runBlocking' src/main` lists only entry points.

## Flow buffer

**Definition.** `buffer(capacity)` runs the upstream flow in a separate
coroutine connected by a channel, so the producer can emit ahead while
the collector is busy ([Flow operators][flowops]; [buffer][buffer]).

**Use when.**

- Both producer and collector take time per element (fetch upstream,
  write downstream), and total time is the sum of both.

**Do not use when.**

- Emission order or backpressure timing is part of the contract: the
  producer must not run ahead, for example because it holds a lock or a
  cursor.
- Buffered elements are large: capacity times element size stays in
  memory.

**Example.**

```kotlin
ticks()          // delay(100) before each of 3 emits
    .buffer()    // default capacity 64 (Channel.BUFFERED)
    .collect { delay(300) }
```

**Cost removed.** The producer waiting on the collector. Virtual time:
1,200 ms without buffer, 1,000 ms with it, same 3 elements.

**Verify.**

1. `verify.sh verify coroutines`: `PASS flow plain` (1,200) and
   `PASS flow buffer` (1,000).

## Flow conflate

**Definition.** `conflate()` is `buffer(1, onBufferOverflow =
BufferOverflow.DROP_OLDEST)`: a slow collector skips intermediate values
and receives the newest ([Flow operators][flowops]; [conflate][conflate]).

**Use when.**

- Only the latest value matters (progress, UI state, sensor readings),
  and the collector is slower than the producer.

**Do not use when.**

- Every element must be processed (events, commands, log lines): values
  are dropped. The oracle shows `[1, 3]` instead of `[1, 2, 3]`.

**Example.**

```kotlin
ticks().conflate().collect { delay(300) }
```

**Cost removed.** Processing of stale elements. Virtual time: 700 ms and
2 elements, against 1,200 ms and 3 without it.

**Verify.**

1. `verify.sh verify coroutines`: `PASS flow conflate`.

## flowOn for upstream context

**Definition.** `flowOn(context)` changes the context of the upstream
flow only. If the dispatcher changes, it collects upstream in a separate
coroutine with a buffer ([Flow operators][flowops]; [flowOn][flowon]).
Calling `withContext` inside `flow { }` to emit from another dispatcher
violates the flow invariant and throws `IllegalStateException`.

**Use when.**

- The producer does blocking or CPU-heavy work (parsing, file reads),
  and the collector must stay on the caller's context.

**Do not use when.**

- The collector is the heavy part: `flowOn` does not move it. Move that
  work with `withContext` inside `collect`, or restructure.
- You rely on unbuffered, lock-step emission: the dispatcher change adds
  a buffer.

**Example.**

```kotlin
flow { emit(Thread.currentThread().name) }
    .flowOn(Dispatchers.Default)
    .collect { println(it) } // runs on the caller's thread
```

Runnable: `upstreamThreadBaseline` (`withContext` inside `flow`) and
`upstreamThreadCandidate`.

**Cost removed.** Heavy upstream work on the collector's thread, without
breaking the flow invariant. Measured: upstream on
`DefaultDispatcher-worker-N`, downstream on `main`; the baseline throws
"Flow invariant is violated".

**Verify.**

1. `verify.sh verify coroutines`: `PASS flow withContext rejected` and
   `PASS flowOn threads`.

## Mutex for critical sections that suspend

**Definition.** `Mutex` suspends a coroutine that waits for the lock
instead of blocking its thread. It is not reentrant, and unlock
happens-before the next successful lock ([Mutex][mutex]). `synchronized`
cannot contain a suspension point: kotlinc rejects it ("the 'delay'
suspension point is inside a critical section", checked locally).

**Use when.**

- A read-modify-write of shared state spans a suspending call (fetch,
  then update a cache entry), or waiters must not block threads.

**Do not use when.**

- The critical section never suspends: use an atomic or `synchronized`
  (next card).
- The same coroutine may lock twice: `Mutex` deadlocks on reentry.

**Example.**

```kotlin
mutex.withLock {
    val read = counter
    delay(1) // suspension inside the read-modify-write
    counter = read + 1
}
```

**Cost removed.** Lost updates. Virtual time, 100 coroutines: without a
lock the counter ends at 1 (all read 0 before any write); with `Mutex`
it ends at 100.

**Verify.**

1. `verify.sh verify coroutines`: `PASS mutex lost updates baseline` (1)
   and `PASS mutex serialized` (100).

## Atomics or synchronized for critical sections that do not suspend

**Definition.** For a short section with no suspension, an
`AtomicInteger`/`AtomicLong` operation or a `synchronized` block needs no
coroutine machinery; the thread blocks only for the instructions in the
section ([shared mutable state][shared]).

**Use when.**

- Coroutines on multi-threaded dispatchers share a counter, flag, or
  small map update, and the section cannot suspend.

**Do not use when.**

- The section suspends (a compile error for `synchronized`) or can block
  for long (I/O under a lock blocks a dispatcher thread).

**Example.**

```kotlin
val counter = AtomicInteger()
List(8) {
    launch(Dispatchers.Default) {
        repeat(10_000) { counter.incrementAndGet() }
    }
}.joinAll()
```

**Cost removed.** Suspension bookkeeping per lock. Both forms are exact
(80,000). JMH, 100 uncontended increments in one `runBlocking`:
`mutexIncrement` 1,974 ± 239.0 ns/op, 296 B/op; `synchronizedIncrement`
1,039 ± 145.3 ns/op, 248 B/op; `atomicIncrement` 834.3 ± 89.2 ns/op,
248 B/op. The 248 B is the `runBlocking` wrapper, present in every
variant.

**Verify.**

1. `verify.sh verify coroutines`: `PASS mutex counter` and
   `PASS atomic counter` (80,000 each, 8 coroutines on `Default`).
1. `BENCH_FILTER=Increment sh assets/examples/verify.sh measure`.

## Channel capacity

**Definition.** The `Channel()` factory's `capacity` defaults to
`RENDEZVOUS`: no buffer, so `send` suspends until `receive`.
`Channel.BUFFERED` has capacity 64 by default (a JVM system property
overrides it). `CONFLATED` keeps one element and drops the oldest.
`UNLIMITED` never suspends the sender ([Channel][channel];
[BUFFERED][buffered]).

**Use when.**

- A producer should run ahead of a slower consumer by a bounded amount
  (batch I/O, pipeline stages): choose a fixed capacity.

**Do not use when.**

- `UNLIMITED` would hide a slow consumer: memory grows without bound.
- The producer must wait for each hand-off because rendezvous is the
  contract, for example request-response over a channel.

**Example.**

```kotlin
val channel = Channel<Int>(Channel.BUFFERED)
launch {
    repeat(5) { channel.send(it) }
    channel.close()
}
for (item in channel) delay(100)
```

Runnable: `producerDoneAt(capacity)`.

**Cost removed.** Producer suspension. Virtual time until the producer
finished 5 sends against a 100 ms consumer: `RENDEZVOUS` 400 ms,
`BUFFERED` 0 ms.

**Verify.**

1. `verify.sh verify coroutines`: `PASS channel rendezvous` (400) and
   `PASS channel buffered` (0).

## Rethrow CancellationException

**Definition.** Suspension points deliver cancellation as
`CancellationException`. "Catching CancellationException can break the
cancellation propagation. If you must catch it, rethrow it"
([cancellation][cancel]). `catch (e: Exception)` and `runCatching`
around a suspending call catch it too.

**Use when.**

- A loop or retry wrapper catches `Exception`/`Throwable` around
  suspending calls.

**Do not use when.**

- Never skip the rethrow. To handle a timeout as a value, use
  `withTimeoutOrNull` instead of catching `TimeoutCancellationException`.

**Example.**

```kotlin
try {
    delay(10)
} catch (e: Exception) {
    if (e is CancellationException) throw e
    log(e)
}
```

Runnable: `iterationsAfterCancel(rethrow)`.

**Cost removed.** Work after cancellation. Virtual time, 50 iterations of
`delay(10)`, cancelled at 25 ms: the swallowing loop ran all 50
iterations (each `delay` threw immediately and was ignored); the
rethrowing loop stopped after 2.

**Verify.**

1. `verify.sh verify coroutines`: `PASS cancellation swallowed` (50) and
   `PASS cancellation rethrown` (2).
1. In the target: `rg -n 'catch \(e: (Exception|Throwable)\)|runCatching'`
   in suspend code, then check each hit for a rethrow.

## ensureActive in CPU-bound loops

**Definition.** Cancellation is cooperative: code that never suspends
never sees it. `ensureActive()` throws `CancellationException` once the
coroutine is cancelled, and `isActive` then returns `false`
([cancellation][cancel]; [ensureActive][ensure]).

**Use when.**

- A coroutine runs a long CPU loop (parsing, hashing, image work) with no
  suspension points and must stop when its scope is cancelled.

**Do not use when.**

- The loop body must complete atomically (a partial write would corrupt
  state): check between units of work, not inside one.

**Example.**

```kotlin
for (chunk in chunks) {
    ensureActive()
    process(chunk)
}
```

Runnable: `chunksAfterCancel(checkActive)`; cancellation arrives while
chunk 1 runs.

**Cost removed.** CPU after cancellation. Measured: without the check all
20 chunks ran; with it, 2.

**Verify.**

1. `verify.sh verify coroutines`: `PASS ensureActive absent` (20) and
   `PASS ensureActive present` (2).

[default]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-default.html
[io]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html
[limited]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html
[basics]: https://kotlinlang.org/docs/coroutines-basics.html
[global]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-global-scope/
[compose]: https://kotlinlang.org/docs/composing-suspending-functions.html
[runblocking]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-blocking.html
[flowops]: https://kotlinlang.org/docs/coroutines-flow-operators.html
[buffer]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/buffer.html
[conflate]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/conflate.html
[flowon]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html
[mutex]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-mutex/
[shared]: https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html
[channel]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/
[buffered]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/-factory/-b-u-f-f-e-r-e-d.html
[cancel]: https://kotlinlang.org/docs/coroutines-cancellation.html
[ensure]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html
[Coroutines.kt]: ../assets/examples/constructs/src/main/kotlin/constructs/Coroutines.kt
