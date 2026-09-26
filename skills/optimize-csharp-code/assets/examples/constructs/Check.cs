// Oracle helpers shared by every construct. A check throws on the first
// mismatch so verify.sh exits nonzero and names the failing construct.
public static class Check
{
    public static int Count { get; private set; }

    public static void Equal<T>(string construct, T expected, T actual)
    {
        Count++;
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException($"{construct}: expected {expected}, got {actual}");
        }
    }

    public static void SequenceEqual<T>(
        string construct,
        IEnumerable<T> expected,
        IEnumerable<T> actual
    )
    {
        Count++;
        if (!expected.SequenceEqual(actual))
        {
            throw new InvalidOperationException($"{construct}: sequences differ");
        }
    }

    // Measures bytes allocated on this thread by `action` after a warmup
    // call, so first-call JIT and static initialization are excluded.
    public static long AllocatedBytes(Action action)
    {
        action();
        long before = GC.GetAllocatedBytesForCurrentThread();
        action();
        return GC.GetAllocatedBytesForCurrentThread() - before;
    }

    public static void NoAllocation(string construct, Action action)
    {
        Count++;
        long bytes = AllocatedBytes(action);
        if (bytes != 0)
        {
            throw new InvalidOperationException($"{construct}: candidate allocated {bytes} bytes");
        }
    }

    public static void AllocatesLess(string construct, Action baseline, Action candidate)
    {
        Count++;
        long before = AllocatedBytes(baseline);
        long after = AllocatedBytes(candidate);
        Console.WriteLine($"ALLOC {construct}: {before} B -> {after} B");
        if (after >= before)
        {
            throw new InvalidOperationException($"{construct}: {after} B is not below {before} B");
        }
    }
}
