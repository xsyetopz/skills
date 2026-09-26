// Concurrency and async constructs. Checks assert the same totals and
// ordering guarantees for baseline and candidate under real threads.
using System.Threading.Channels;
using BenchmarkDotNet.Attributes;

public sealed class MonitorCounter
{
    private readonly object gate = new();
    private long total;

    public void Add(long value)
    {
        lock (gate)
        {
            total += value;
        }
    }

    public long Total
    {
        get
        {
            lock (gate)
            {
                return total;
            }
        }
    }
}

// System.Threading.Lock (.NET 9+): the C# 13+ `lock` statement recognizes the
// type and calls EnterScope instead of Monitor.Enter/Exit.
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

    public long Total
    {
        get
        {
            lock (gate)
            {
                return total;
            }
        }
    }
}

public sealed class InterlockedCounter
{
    private long total;

    public void Add(long value) => Interlocked.Add(ref total, value);

    public long Total => Interlocked.Read(ref total);
}

public static class ParallelAggregation
{
    public static long BaselineSum(int[] values)
    {
        long total = 0;
        Parallel.For(0, values.Length, i => Interlocked.Add(ref total, values[i]));
        return total;
    }

    // One Interlocked operation per worker instead of one per element.
    public static long CandidateSum(int[] values)
    {
        long total = 0;
        Parallel.For(
            0,
            values.Length,
            localInit: () => 0L,
            body: (i, _, local) => local + values[i],
            localFinally: local => Interlocked.Add(ref total, local)
        );
        return total;
    }
}

public static class Pipelines
{
    // Unbounded handoff: a fast producer can grow the queue without limit.
    public static async Task<long> BaselineAsync(int items)
    {
        var channel = Channel.CreateUnbounded<int>();
        Task producer = Task.Run(async () =>
        {
            for (int i = 0; i < items; i++)
            {
                await channel.Writer.WriteAsync(i);
            }
            channel.Writer.Complete();
        });
        long sum = 0;
        await foreach (int item in channel.Reader.ReadAllAsync())
        {
            sum += item;
        }
        await producer;
        return sum;
    }

    // Bounded handoff: WriteAsync waits when `capacity` items are queued,
    // which caps memory and applies backpressure to the producer.
    public static async Task<long> CandidateAsync(int items, int capacity)
    {
        var channel = Channel.CreateBounded<int>(
            new BoundedChannelOptions(capacity)
            {
                SingleReader = true,
                SingleWriter = true,
                FullMode = BoundedChannelFullMode.Wait,
            }
        );
        Task producer = Task.Run(async () =>
        {
            for (int i = 0; i < items; i++)
            {
                await channel.Writer.WriteAsync(i);
            }
            channel.Writer.Complete();
        });
        long sum = 0;
        await foreach (int item in channel.Reader.ReadAllAsync())
        {
            sum += item;
        }
        await producer;
        return sum;
    }
}

public static class AsyncBoundaries
{
    // Blocks a thread-pool thread for the whole delay (sync-over-async).
    public static int BaselineBlocking(int delayMs)
    {
        return Task.Delay(delayMs).ContinueWith(_ => 1).Result;
    }

    public static async Task<int> CandidateAsync(int delayMs)
    {
        // Library code: the continuation does not need the caller's
        // SynchronizationContext, so skip the post back to it.
        await Task.Delay(delayMs).ConfigureAwait(false);
        return 1;
    }
}

public static class ConcurrencyChecks
{
    public static void Run()
    {
        const int threads = 8;
        const int perThread = 20_000;
        long expected = threads * (long)perThread * 3;

        var monitor = new MonitorCounter();
        var lockType = new LockCounter();
        var interlocked = new InterlockedCounter();
        Check.Equal(
            "lock-type",
            expected,
            Hammer(monitor.Add, () => monitor.Total, threads, perThread)
        );
        Check.Equal(
            "lock-type",
            expected,
            Hammer(lockType.Add, () => lockType.Total, threads, perThread)
        );
        Check.Equal(
            "interlocked",
            expected,
            Hammer(interlocked.Add, () => interlocked.Total, threads, perThread)
        );

        int[] values = [.. Enumerable.Range(0, 200_000)];
        long serial = values.Sum(v => (long)v);
        Check.Equal("parallel-local", serial, ParallelAggregation.BaselineSum(values));
        Check.Equal("parallel-local", serial, ParallelAggregation.CandidateSum(values));

        long pipelineExpected = 9999L * 10000 / 2;
        Check.Equal(
            "bounded-channel",
            pipelineExpected,
            Pipelines.BaselineAsync(10_000).GetAwaiter().GetResult()
        );
        Check.Equal(
            "bounded-channel",
            pipelineExpected,
            Pipelines.CandidateAsync(10_000, 64).GetAwaiter().GetResult()
        );

        Check.Equal(
            "sync-over-async",
            AsyncBoundaries.BaselineBlocking(1),
            AsyncBoundaries.CandidateAsync(1).GetAwaiter().GetResult()
        );
    }

    private static long Hammer(Action<long> add, Func<long> read, int threads, int perThread)
    {
        var workers = new Thread[threads];
        for (int t = 0; t < threads; t++)
        {
            workers[t] = new Thread(() =>
            {
                for (int i = 0; i < perThread; i++)
                {
                    add(3);
                }
            });
            workers[t].Start();
        }
        foreach (Thread worker in workers)
        {
            worker.Join();
        }
        return read();
    }
}

[MemoryDiagnoser]
public class ConcurrencyBenchmarks
{
    private readonly MonitorCounter monitor = new();
    private readonly LockCounter lockType = new();
    private readonly InterlockedCounter interlocked = new();
    private readonly int[] values = [.. Enumerable.Range(0, 1 << 20)];

    [Benchmark(Baseline = true)]
    public void MonitorAdd() => monitor.Add(1);

    [Benchmark]
    public void LockTypeAdd() => lockType.Add(1);

    [Benchmark]
    public void InterlockedAdd() => interlocked.Add(1);

    [Benchmark]
    public long PerItemInterlocked() => ParallelAggregation.BaselineSum(values);

    [Benchmark]
    public long ThreadLocalSums() => ParallelAggregation.CandidateSum(values);
}
