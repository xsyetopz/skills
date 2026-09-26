# Concurrency constructs

Each card chooses where `Future` and parallel collection work runs.
Examples are in `assets/examples/constructs/Concurrency.scala` and
`Collections.scala`. `ConcurrencyChecks` asserts results and the peak
number of concurrently running tasks (an `AtomicInteger` gauge), because
wall time on a shared machine is not reproducible.

Tier: executed locally (`verify.sh verify`; `.par` also by `measure`).
The peak-concurrency assertions depend on `ForkJoinPool` behavior the
Futures documentation does not guarantee, so they can fail on another
machine without a Scala change. Measured on: Apple M1 Max (10 cores,
`availableProcessors` 10), macOS arm64, OpenJDK 25.0.4.1, Scala 3.8.4,
scala-parallel-collections 1.2.0. Scala.js runs on a single-threaded
event loop; none of the thread-count results apply there.

## Contents

- ExecutionContext.global for CPU-bound futures
- blocking inside ExecutionContext.global
- Dedicated ExecutionContext for blocking I/O
- ExecutionContext.parasitic for cheap callbacks
- Parallel collections with .par

## ExecutionContext.global for CPU-bound futures

**Definition.** `ExecutionContext.global` is backed by a `ForkJoinPool`
whose parallelism defaults to `Runtime.availableProcessors`, adjustable
with the system properties `scala.concurrent.context.minThreads`,
`numThreads`, and `maxThreads` ([Futures][futures]).

**Use when.**

- Future bodies are short and CPU-bound (parsing, computing, combining
  results). This is the default pool.

**Do not use when.**

- Bodies block (JDBC, file I/O, `Thread.sleep`, `Await.result`) without
  `blocking`: the documentation warns the pool can be "starved, and no
  computation can proceed". Measured: 40 sleeping futures on global
  without `blocking` never had more than 10 running at once.

**Example.**

```scala
def baseline(tasks: Int, g: Gauge)(using ExecutionContext): Int =
  val fs = List.fill(tasks)(Future(g.sleepy(50)))
  Await.result(Future.sequence(fs), 60.seconds).sum
```

Runnable: `BlockingFutures.baseline` in `Concurrency.scala`.

**Cost removed.** None; this card sets the default and its limit. A
gauge or thread dump (`jcmd <pid> Thread.print`) shows at most
`availableProcessors` running workers.

**Verify.**

1. `PASS futures-baseline` (all 40 results).
1. `PASS global without blocking stays at parallelism (peak 10,
   availableProcessors 10)`.

## blocking inside ExecutionContext.global

**Definition.** `scala.concurrent.blocking { ... }` notifies the current
execution context that the enclosed code blocks; `global` implements it
with a `ForkJoinPool.ManagedBlocker` and may add threads beyond its
parallelism level ([Futures][futures]).

**Use when.**

- A few short blocking calls run on `global` and cannot practically
  move.

**Do not use when.**

- Blocking calls are many or long-lasting: the documentation says the
  pool "might not spawn new workers as you would expect" and "when new
  workers are created they can be as many as 32767"; it recommends a
  dedicated execution context for long-lasting blocking.
- The context is a fixed thread pool from `ExecutionContext.fromExecutor`:
  `blocking` does nothing there ([Futures][futures]).

**Example.**

```scala
def candidate(tasks: Int, g: Gauge)(using ExecutionContext): Int =
  val fs = List.fill(tasks)(Future(blocking(g.sleepy(50))))
  Await.result(Future.sequence(fs), 60.seconds).sum
```

Runnable: `BlockingFutures.candidate` in `Concurrency.scala`.

**Cost removed.** Queueing behind blocked workers. Measured: peak
concurrency 40 of 40 tasks with `blocking`, 10 without.

**Verify.**

1. `PASS futures-blocking`.
1. `PASS blocking lets global exceed parallelism (peak 40, ...)`.

## Dedicated ExecutionContext for blocking I/O

**Definition.** `ExecutionContext.fromExecutor(Executors
.newFixedThreadPool(n))` gives blocking work its own bounded pool, so it
cannot starve `global` ([Futures][futures]).

**Use when.**

- Futures perform blocking I/O (JDBC, legacy clients, file system).
- Concurrent blocking calls need a hard upper bound, such as the database
  connection pool size.

**Do not use when.**

- The work is CPU-bound: threads beyond the core count add context
  switches.
- The pool would be created per request or never shut down: threads
  leak. Create it once and `shutdown()` it when the application stops.

**Example.**

```scala
def run(tasks: Int, threads: Int, g: Gauge): Int =
  val pool = Executors.newFixedThreadPool(threads)
  try
    given ExecutionContext = ExecutionContext.fromExecutor(pool)
    val fs = List.fill(tasks)(Future(g.sleepy(50)))
    Await.result(Future.sequence(fs), 60.seconds).sum
  finally
    pool.shutdown()
    pool.awaitTermination(10, TimeUnit.SECONDS)
```

Runnable: `DedicatedPool` in `Concurrency.scala`.

**Cost removed.** Starvation of CPU-bound work on `global`; `threads`
bounds blocking concurrency. Measured: peak 40 with a 40-thread pool.

**Verify.**

1. `PASS dedicated-pool`.
1. `PASS dedicated pool runs blocking tasks beyond the core count (peak
   40 of 40, cores 10)`; in a real service, compare the pool size with
   the connection pool.

## ExecutionContext.parasitic for cheap callbacks

**Definition.** `ExecutionContext.parasitic` runs submitted work on the
thread that calls `execute` and trampolines nested calls (it is absent
from the Scala 2.12 sources). Its scaladoc says to "only ever execute
logic which will quickly return control to the caller" and never to
block ([ExecutionContext][ec-api], [source][ec-src]).

**Use when.**

- A `map` or `onComplete` callback is trivial (field access, wrapping),
  so a hop to another pool costs more than the callback.

**Do not use when.**

- The callback blocks or runs long: it runs on whichever thread completed
  the future, possibly a pool or I/O thread, and the scaladoc lists
  deadlocks and "severe performance problems" as symptoms of misuse.
- The callback needs a particular thread (UI, actor): the executing
  thread is non-deterministic.

**Example.**

```scala
def callbackThread(ec: ExecutionContext): String =
  val done = Future.successful(41)
  val f = done.map(_ => Thread.currentThread.getName)(using ec)
  Await.result(f, 10.seconds)
```

Runnable: `Parasitic` in `Concurrency.scala`.

**Cost removed.** One task submission and thread hop per callback.
Measured: with `parasitic` the callback ran on the calling thread; with
`global` it ran on `scala-execution-context-global-<n>`.

**Verify.**

1. `PASS parasitic runs on the calling thread`.
1. `PASS global hops to a pool thread (callback on ...)`.

## Parallel collections with .par

**Definition.** Since Scala 2.13, parallel collections are a separate
module. `.par` needs the
`org.scala-lang.modules::scala-parallel-collections` dependency and
`import scala.collection.parallel.CollectionConverters.*`
([module README][par-readme], [overview][par-overview]).

**Use when.**

- A pure, CPU-bound transformation or associative reduction runs over a
  large in-memory collection, and cores are idle.

**Do not use when.**

- The operation has side effects or is not associative: the overview
  lists both as sources of non-determinism. `Double` addition is not
  associative (asserted by `PASS double addition is not associative`),
  so a parallel `sum` of doubles can differ from the sequential one.
- The collection is small: splitting and combining cost more than the
  work.
- A server already uses all cores for requests: `.par` competes with
  them.

**Example.**

```scala
//> using dep org.scala-lang.modules::scala-parallel-collections:1.2.0
import scala.collection.parallel.CollectionConverters.*

def baseline(xs: Vector[Long]): Long = xs.map(x => x * x % 7).sum
def candidate(xs: Vector[Long]): Long = xs.par.map(x => x * x % 7).sum
```

Runnable: `ParallelSum` in `Collections.scala`.

**Cost removed.** Wall time on idle cores for large inputs. JMH,
2,000,000 elements, 10 cores shared with other builds: `sequentialSum`
16.50 ± 2.43 ms/op, `parallelSum` 8.70 ± 1.06 ms/op. The parallel
version allocated more (66.5 MB/op versus 57.3 MB/op). The first use
under JDK 25 printed a `sun.misc.Unsafe::objectFieldOffset` deprecation
warning from `scala.runtime.LazyVals$` ([JEP 498][jep498]: JDK 24+ warns
on first use of the memory-access methods of `sun.misc.Unsafe`).

**Verify.**

1. `PASS parallel-sum` (exact for `Long`).
1. `BENCH_FILTER='Pairs.(sequential|parallel)Sum' sh
   assets/examples/verify.sh measure`.

[futures]: https://docs.scala-lang.org/overviews/core/futures.html
[ec-api]: https://www.scala-lang.org/api/3.x/scala/concurrent/ExecutionContext$.html
[ec-src]: https://github.com/scala/scala/blob/2.13.x/src/library/scala/concurrent/ExecutionContext.scala
[par-readme]: https://github.com/scala/scala-parallel-collections
[par-overview]: https://docs.scala-lang.org/overviews/parallel-collections/overview.html
[jep498]: https://openjdk.org/jeps/498
