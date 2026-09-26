# Concurrency constructs

Each card changes how threads share work or state. Runnable pairs are in
[`Concurrency.java`][example-src].
`Verify.concurrency()` checks results and the deterministic claims, and
`ConcurrencyBench` measures counter throughput with JMH.

Measured on: Apple M1 Max (10 cores), macOS arm64, OpenJDK 25.0.4.1,
JMH 1.37, shared machine (load average 4 to 91). Timings are
machine-specific.

## Contents

- Virtual threads for blocking tasks
- Virtual thread pinning after JEP 491
- ConcurrentHashMap computeIfAbsent
- LongAdder for contended counters

## Virtual threads for blocking tasks

**Definition.** A virtual thread (final in JDK 21, [JEP 444][jep444]) is
a `java.lang.Thread` that the JDK schedules onto a small pool of carrier
platform threads. When it blocks in a JDK blocking call (sleep, socket
I/O, `BlockingQueue.take`, locks), it unmounts and frees the carrier.
`Executors.newVirtualThreadPerTaskExecutor()` starts one per task.

**Use when.**

- Many concurrent tasks spend most of their time blocked (HTTP/JDBC
  calls, sleeps, queue waits), and a fixed platform pool caps throughput:
  tasks wait in the executor queue while pool threads sit blocked.
- Thread dumps show pool threads parked in I/O and a growing queue.

**Do not use when.**

- The work is CPU-bound: JEP 444 states that virtual threads improve
  throughput, not latency, and do not make code run faster. A CPU-bound
  pool of `availableProcessors()` threads is already saturated.
- You would pool them: JEP 444 says virtual threads "should never be
  pooled". Limit concurrency to a downstream resource with a `Semaphore`.
- Each task caches an expensive object in a `ThreadLocal`: with one
  thread per task the cache never hits, and the object is recreated per
  task (JEP 444 thread-local guidance).
- The blocking happens in native code or a class initializer: the carrier
  stays pinned (see the [next card](#virtual-thread-pinning-after-jep-491)).

**Example.**

```java
public static long runBlocking(ExecutorService executor, int tasks,
        Duration block) throws Exception {
    try (executor) {
        List<Future<Integer>> futures = new ArrayList<>(tasks);
        for (int i = 0; i < tasks; i++) {
            int id = i;
            futures.add(executor.submit(() -> {
                sleep(block); // stands in for a blocking I/O call
                return id;
            }));
        }
        long sum = 0;
        for (Future<Integer> f : futures) {
            sum += f.get();
        }
        return sum;
    }
}
// baseline: runBlocking(Executors.newFixedThreadPool(20), 400, 50 ms)
// candidate: runBlocking(Executors.newVirtualThreadPerTaskExecutor(), ...)
```

Runnable: `Concurrency.runBlocking` and `Verify.concurrency()`.

**Cost removed.** Queueing behind blocked pool threads. Wall time for 400
tasks that each block 50 ms: a 20-thread pool needs at least
400 / 20 x 50 ms = 1,000 ms by arithmetic. Measured:
`fixedPool(20)=1070ms virtualPerTask=63ms`, and on a second run `1101ms`
versus `69ms` (machine-specific, shared machine).

**Verify.**

1. `sh assets/examples/verify.sh verify` checks that both executors
   return the same sum (every task ran exactly once).
1. The same run asserts `virtualMs * 4 < platformMs` and prints the
   `WALL blocking ...` line. In an application, compare throughput and
   the `jdk.VirtualThreadPinned` and `jdk.VirtualThreadSubmitFailed` JFR
   events.

## Virtual thread pinning after JEP 491

**Definition.** A virtual thread is *pinned* when it blocks but cannot
unmount, so its carrier blocks too. Since JDK 24, [JEP 491][jep491] lets
virtual threads unmount inside `synchronized`. Pinning remains when a
virtual thread blocks inside a class initializer, while waiting for
another thread's class initialization, during class loading, or in
native code that calls back into Java and then blocks. JFR's
`jdk.VirtualThreadPinned` event records it with a `pinnedReason`.

**Use when.**

- Deciding whether to rewrite `synchronized` to `ReentrantLock` for
  virtual threads: on JDK 24+ unmounting no longer needs that rewrite,
  and JEP 491 recommends `synchronized` where practical.
- JFR shows `jdk.VirtualThreadPinned` events: read the `pinnedReason` and
  stack to find the remaining cause.

**Do not use when.**

- The target JDK is 21 to 23: `synchronized` still pins there, and the
  fix is `ReentrantLock` around blocking calls, or an upgrade.
- You rely on `-Djdk.tracePinnedThreads`: JEP 491 removed it, and setting
  it has no effect. Use the JFR event.

**Example.**

```java
static final class SlowInit {
    static final int VALUE;
    static {
        Concurrency.sleep(Duration.ofMillis(60)); // blocks in <clinit>
        VALUE = 7;
    }
}

static void pinning() throws InterruptedException {
    Object lock = new Object();
    List<Thread> threads = new ArrayList<>();
    for (int i = 0; i < 8; i++) {
        threads.add(Thread.ofVirtual().start(() -> {
            synchronized (lock) {                  // no pin on JDK 24+
                Concurrency.sleep(Duration.ofMillis(30));
            }
        }));
    }
    for (Thread t : threads) {
        t.join();
    }
    Thread.ofVirtual().start(() -> System.out.println(SlowInit.VALUE))
        .join();                                   // pins: class init
}
```

Runnable: `Workload.pinning()`.

**Cost removed.** Blocked carriers. JFR result on JDK 25: exactly one
`jdk.VirtualThreadPinned` event, with
`pinnedReason = "VM call to example.Workload$SlowInit.<clinit> on stack"`.
The eight `synchronized` sleeps (30 ms each, above the event's 20 ms
default threshold per JEP 444) produced none.

**Verify.**

1. `sh assets/examples/verify.sh tools` records `Workload pinning` with
   `-XX:StartFlightRecording` and fails unless there is exactly one
   `jdk.VirtualThreadPinned` event and it names `SlowInit.<clinit>`.
1. In an application: `jfr print --events jdk.VirtualThreadPinned
   rec.jfr` before and after the change; the count must drop.

## ConcurrentHashMap computeIfAbsent

**Definition.** `ConcurrentHashMap.computeIfAbsent(key, f)` performs the
whole lookup-compute-insert atomically: `f` "is invoked exactly once per
invocation of this method if the key is absent, else not at all"
([javadoc][chm]).

**Use when.**

- A cache or memo does `get`, then computes, then `put`/`putIfAbsent`:
  concurrent misses compute the same value several times, and with `put`
  callers can see different instances.
- The value is expensive or must be unique per key (a connection, a
  `LongAdder`, a compiled pattern).

**Do not use when.**

- The mapping function is slow or blocking: other updates to the same
  bin wait while it runs, and the javadoc says the computation "should be
  short and simple". Store a `CompletableFuture` or use a loading cache
  instead.
- The mapping function touches the same map: the javadoc forbids it, and
  the map may throw `IllegalStateException` ("Recursive update").
- The target is JDK 8: [JDK-8161372][jdk8161372] ("computeIfAbsent(k,f)
  locks bin when k present") was fixed in JDK 9. On 8, check `get` first.

**Example.**

```java
/** Check-then-act: two threads can both miss and both compute. */
public V getOrComputeRacy(K key) {
    V value = map.get(key);
    if (value == null) {
        V created = factory.apply(key);
        V previous = map.putIfAbsent(key, created);
        value = previous == null ? created : previous;
    }
    return value;
}

/** Atomic: the factory runs at most once per absent key. */
public V getOrCompute(K key) {
    return map.computeIfAbsent(key, factory);
}
```

Runnable: `Concurrency.Memo` and `Concurrency.factoryCalls`.

**Cost removed.** Duplicate factory calls. Measured: 8 threads over the
same 50 keys (the factory sleeps 2 ms to widen the race) ran the factory
400 and 390 times with `get`+`putIfAbsent` in two runs, and exactly 50
times with `computeIfAbsent`. The racy count varies by run; the atomic
count does not.

**Verify.**

1. `sh assets/examples/verify.sh verify` checks that every caller
   received `"v" + k`, and asserts `computeIfAbsent` calls == keys (50).
1. The printed `FACTORY CALLS` line shows the baseline count. In your
   code, count factory invocations under load (a counter or a JFR custom
   event).

## LongAdder for contended counters

**Definition.** `LongAdder` keeps a base value plus a set of cells that
contending threads update separately, and sums them on `sum()`. Its
javadoc says that under high contention "expected throughput of this
class is significantly higher" than `AtomicLong`, "at the expense of
higher space consumption", and that `sum()` is "NOT an atomic snapshot"
([javadoc][longadder]).

**Use when.**

- Several threads increment one statistics counter on a hot path
  (request counts, metrics), and a profile shows time in the `AtomicLong`
  increment.
- Readers need a total occasionally, not a consistent snapshot.

**Do not use when.**

- The value drives control flow (sequence numbers, IDs, `compareAndSet`
  loops, limits): `LongAdder` has no `compareAndSet`, and `sum()` can
  miss concurrent updates.
- There is one writer thread: the javadoc states that both classes behave
  similarly under low contention, and `LongAdder` uses more memory.

**Example.**

```java
@State(Scope.Benchmark)          // one instance shared by all threads
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Threads(4)
public class ConcurrencyBench {
    private final Concurrency.Counters counters = new Concurrency.Counters();

    @Benchmark
    public void counterAtomicLong() {
        counters.incrementAtomic();       // AtomicLong.incrementAndGet
    }

    @Benchmark
    public void counterLongAdder() {
        counters.incrementAdder();        // LongAdder.increment
    }
}
```

Runnable: `ConcurrencyBench.java`.

**Cost removed.** CAS retries and cache-line transfers on one contended
field. Measured, 4 threads on one shared instance, two runs:
`counterAtomicLong` 66.972 ± 7.506 and 28.594 ± 1.846 ops/us;
`counterLongAdder` 113.143 ± 47.089 and 471.347 ± 68.505 ops/us (first
run 1 fork, second 3 forks). The ratio moved with machine load, but the
adder led in both runs, and the second run's intervals do not overlap.

**Verify.**

1. `sh assets/examples/verify.sh verify` runs 4 threads x 100,000
   increments on both counters and requires 400,000 from each.
1. `BENCH_FILTER=ConcurrencyBench sh assets/examples/verify.sh measure`:
   `counterLongAdder` ops/us must exceed `counterAtomicLong` beyond the
   error columns. Run with `-t 1` via `JMH_ARGS='-t 1'` to see the
   uncontended case.

[jep444]: https://openjdk.org/jeps/444
[jep491]: https://openjdk.org/jeps/491
[chm]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html#computeIfAbsent(K,java.util.function.Function)
[jdk8161372]: https://bugs.openjdk.org/browse/JDK-8161372
[longadder]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html
[example-src]: ../assets/examples/jmh/src/main/java/example/Concurrency.java
