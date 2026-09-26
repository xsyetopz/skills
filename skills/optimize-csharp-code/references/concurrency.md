# Concurrency and async constructs

Examples live in
[`Concurrency.cs`](../assets/examples/constructs/Concurrency.cs);
`ConcurrencyChecks.Run` hammers each construct from 8 threads and compares
totals. Measured on an Apple M1 Max (10 cores), .NET 10.0.11 Arm64,
BenchmarkDotNet 0.15.8 `--job short`; numbers are machine-specific. The
lock rows are single-threaded (uncontended).

## Contents

- System.Threading.Lock
- Interlocked instead of a lock
- Parallel.For with thread-local state
- Bounded Channel of T
- Async all the way instead of sync-over-async
- ConfigureAwait(false) in library code

## System.Threading.Lock

**Definition.** `System.Threading.Lock` (.NET 9+) is a dedicated mutual
exclusion type. When the C# 13+ `lock` statement's operand has static type
`Lock`, the compiler calls `Lock.EnterScope()` and disposes the scope
instead of using `Monitor.Enter`/`Exit` on an object header
([Lock](https://learn.microsoft.com/en-us/dotnet/api/system.threading.lock),
[lock statement][lock-statement]).

**Use when.**

- Code uses a private `object` only as a lock and targets .NET 9+: the
  type documents intent and lets the runtime avoid object-header monitor
  state.

**Do not use when.**

- The field is typed `object` or passed as `object`: the compiler falls
  back to `Monitor` and warns (CS9216), so the change does nothing.
- The code needs `Monitor.Wait`/`Pulse`: `Lock` does not support them.
- The goal is speed without a measurement. Measured uncontended:
  `LockTypeAdd` 15.6 ns versus 14.7 ns for `MonitorAdd` (within this run's
  error). Adopt it for clarity, not speed, unless a contended benchmark
  shows otherwise.

**Example.**

```csharp
public sealed class LockCounter
{
    private readonly Lock gate = new();
    private long total;

    public void Add(long value)
    {
        lock (gate)
        {
            total += value;
        }
    }
}
```

**Cost removed.** Monitor bookkeeping on the object header. Measure under
the real contention level.

**Verify.**

1. Behavior: `Check.Equal("lock-type", ...)` after 8 threads × 20,000 adds.
1. Compiler binding: build with warnings as errors (the example project
   does) so CS9216 fails the build if the `Lock` is converted to `object`.
1. Benefit: benchmark with the production thread count, not only
   single-threaded.

## Interlocked instead of a lock

**Definition.** `Interlocked.Add`, `Increment`, `CompareExchange`, and
`Read` perform one atomic read-modify-write on a single 32- or 64-bit
location without taking a lock
([Interlocked]).

**Use when.**

- The protected state is a single numeric field or a single reference swap.

**Do not use when.**

- Two or more fields must change together (a count and a sum; a list and
  its size): separate atomics expose torn intermediate states.
- Many cores update the field continuously: the cache line ping-pongs.
  Aggregate per thread instead (next card).

**Example.**

```csharp
public sealed class InterlockedCounter
{
    private long total;

    public void Add(long value) => Interlocked.Add(ref total, value);

    public long Total => Interlocked.Read(ref total);
}
```

`Interlocked.Read` matters on 32-bit processes, where a plain 64-bit read is
not atomic.

**Cost removed.** Lock acquire/release. Measured uncontended: `MonitorAdd`
14.7 ns, `InterlockedAdd` 7.1 ns.

**Verify.**

1. Behavior: the 8-thread hammer total must equal 480,000.
1. Invariant review: list every field the lock protected. If there is
   more than one, do not apply this card.

## Parallel.For with thread-local state

**Definition.** The `Parallel.For` overload with `localInit`, `body`, and
`localFinally` gives each worker a private accumulator and merges it once
per worker, instead of synchronizing per element
([Parallel.For with thread-local variables][parallel-for-local]).

**Use when.**

- A parallel loop performs an `Interlocked` operation or takes a lock per
  element to update a shared result.

**Do not use when.**

- The merge is not associative/commutative (ordered concatenation,
  floating-point sums that must be reproducible bit-for-bit).
- The per-element work is tiny and the input small: parallel overhead
  dominates. Compare with a sequential span loop.

**Example.**

```csharp
public static long CandidateSum(int[] values)
{
    long total = 0;
    Parallel.For(0, values.Length,
        localInit: () => 0L,
        body: (i, _, local) => local + values[i],
        localFinally: local => Interlocked.Add(ref total, local));
    return total;
}
```

**Cost removed.** Cross-core contention on one cache line per element.
Measured, 1,048,576 ints: `PerItemInterlocked` 79.7 ms,
`ThreadLocalSums` 1.22 ms.

**Verify.**

1. Behavior: the oracle compares both against a sequential `Sum` over
   200,000 values.
1. Benefit: the two benchmark rows. Also compare with a sequential loop to
   confirm parallelism pays at all.

## Bounded Channel of T

**Definition.** `Channel.CreateBounded<T>(capacity)` creates an async
producer/consumer queue that holds at most `capacity` items. With
`BoundedChannelFullMode.Wait`, `WriteAsync` waits until space frees,
which applies backpressure
([System.Threading.Channels][system-threading-channels]).

**Use when.**

- A producer can outpace its consumer (ingest, log shipping, work queues)
  and memory growth or GC pressure appears under load.
- There is one reader or one writer: set `SingleReader`/`SingleWriter` so
  the implementation uses cheaper synchronization.

**Do not use when.**

- Dropping or waiting is unacceptable and the producer cannot slow down.
  Choose a dropping `FullMode` (`DropOldest`, `DropNewest`, `DropWrite`)
  only if the contract allows losing items.
- Several consumers read: `SingleReader = true` then makes behavior
  undefined by contract.

**Example.**

```csharp
var channel = Channel.CreateBounded<int>(new BoundedChannelOptions(64)
{
    SingleReader = true,
    SingleWriter = true,
    FullMode = BoundedChannelFullMode.Wait,
});
```

Full producer/consumer pair: `Pipelines.CandidateAsync`.

**Cost removed.** Unbounded queue growth. Watch peak managed heap
(`dotnet-counters monitor --counters System.Runtime`,
`dotnet.gc.last_collection.heap.size`) under a
producer-faster-than-consumer load; the bounded version stays flat.

**Verify.**

1. Behavior: the oracle sums 10,000 items through both channels (no loss,
   no duplication).
1. Benefit: run the service load test with counters and compare peak heap
   and GC count.

## Async all the way instead of sync-over-async

**Definition.** Blocking on a task (`.Result`, `.Wait()`,
`GetAwaiter().GetResult()`) holds a thread for the task's whole duration;
`await` releases it. Under load, blocked thread-pool threads cause
thread-pool starvation, and blocking deadlocks under single-threaded
synchronization contexts
([async guidance][async-guidance]).

**Use when.**

- `dotnet-counters` shows a growing `dotnet.thread_pool.queue.length` and
  `dotnet.thread_pool.thread.count` climbing while CPU is low.
- Stack traces show threads parked in `Task.Wait`/`.Result`.

**Do not use when.**

- The entry point is truly synchronous (a `Main` without async support,
  a legacy synchronous interface that cannot change). Isolate the block at
  that one boundary instead of spreading it.

**Example.**

```csharp
public static async Task<int> CandidateAsync(int delayMs)
{
    await Task.Delay(delayMs).ConfigureAwait(false);
    return 1;
}
```

**Cost removed.** Blocked threads and thread-pool injection delay. Compare
`dotnet.thread_pool.thread.count` and `dotnet.thread_pool.queue.length`
under the same load.

**Verify.**

1. Behavior: the oracle compares results of both forms.
1. Find remaining blocks: `rg -n '\.Result\b|\.Wait\(\)|GetResult\(\)' src/`.
1. Benefit: counters under load before and after.

## ConfigureAwait(false) in library code

**Definition.** `await task.ConfigureAwait(false)` tells the awaiter not to
capture the current `SynchronizationContext`/`TaskScheduler`, so the
continuation runs on a thread-pool thread instead of being posted back
([ConfigureAwait FAQ][configureawait-faq]).

**Use when.**

- General-purpose library code that UI or legacy ASP.NET contexts can
  call, and that touches no context-bound state after the await.

**Do not use when.**

- The code after the await touches UI controls or context-bound state.
- Application code in ASP.NET Core or console apps: there is no
  `SynchronizationContext`, so it has no effect.

**Example.** From `constructs/Concurrency.cs`:

```csharp
public static async Task<int> CandidateAsync(int delayMs)
{
    // Library code: the continuation does not need the caller's
    // SynchronizationContext, so skip the post back to it.
    await Task.Delay(delayMs).ConfigureAwait(false);
    return 1;
}
```

**Cost removed.** A post to the captured context per await (UI message
loop hop). Check UI-thread time in a profiler, or that deadlocks
disappear when callers block.

**Verify.**

1. `rg -n 'await ' src/Library | rg -v ConfigureAwait` lists awaits
   without it. Review each.
1. Tests that run the library under a single-threaded
   `SynchronizationContext` must not deadlock.

[lock-statement]: https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/lock
[interlocked]: https://learn.microsoft.com/en-us/dotnet/api/system.threading.interlocked
[parallel-for-local]: https://learn.microsoft.com/en-us/dotnet/standard/parallel-programming/how-to-write-a-parallel-for-loop-with-thread-local-variables
[system-threading-channels]: https://learn.microsoft.com/en-us/dotnet/core/extensions/channels
[async-guidance]: https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios
[configureawait-faq]: https://devblogs.microsoft.com/dotnet/configureawait-faq/
