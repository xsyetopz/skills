using System;
using System.Buffers;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using System.Threading.Tasks.Sources;

public static class Semantics
{
    private static bool Contract(bool bad, int topic)
    {
        switch (topic)
        {
            case 1: // Identifier comparison is ordinal, not UI-culture collation.
                return bad
                    ? string.Compare("FILE", "file", true, CultureInfo.GetCultureInfo("tr-TR")) == 0
                    : string.Equals("FILE", "file", StringComparison.OrdinalIgnoreCase);
            case 2: // Repeated result reads must not enumerate a side-effecting source again.
                int calls = 0;
                var source = new[] {1, 2}.Select(value => { calls++; return value; });
                if (bad) { _ = source.ToArray(); _ = source.ToArray(); }
                else { var cached = source.ToArray(); _ = cached.Length; _ = cached.Length; }
                return calls == 2;
            case 3: // Snapshot rather than alias.
                int[] owner = {1, 2};
                int[] snapshot = bad ? owner : owner.AsSpan().ToArray();
                owner[0] = 9;
                return snapshot[0] == 1;
            case 4: // A single-use ValueTask source cannot be consumed twice.
                var pending = new SingleUseSource().Read();
                try
                {
                    if (bad) { _ = pending.Result; _ = pending.Result; }
                    else { Task<int> reusable = pending.AsTask(); _ = reusable.Result; _ = reusable.Result; }
                    return true;
                }
                catch (InvalidOperationException) { return false; }
            case 5: // Deliberately deterministic pool: Shared reuse is not guaranteed.
                var pool = new OneBufferPool();
                int[] buffer = pool.Rent(1); buffer[0] = 42;
                pool.Return(buffer, clearArray: !bad);
                int[] next = pool.Rent(1);
                bool cleared = next[0] == 0;
                pool.Return(next, true);
                return cleared;
            case 6: // Any-bit is not all-bit enum membership; zero mask also matches.
                const int value = 1, flag = 3;
                bool contains = bad ? (value & flag) != 0 : (value & flag) == flag;
                return !contains;
            case 7: // Broad recovery must not turn cancellation into success.
                try
                {
                    if (bad) { try { throw new OperationCanceledException(); } catch (Exception) {} }
                    else throw new OperationCanceledException();
                    return false;
                }
                catch (OperationCanceledException) { return true; }
            case 8: // This contract rejects overflow rather than wrapping.
                int maximum = int.MaxValue;
                try { _ = bad ? unchecked(maximum + 1) : checked(maximum + 1); return false; }
                catch (OverflowException) { return true; }
            default: throw new ArgumentOutOfRangeException(nameof(topic));
        }
    }
    public static int Run(string mode, int topic)
    {
        if (mode != "red" && mode != "green") throw new ArgumentException("red|green TOPIC");
        bool pass = Contract(mode == "red", topic);
        Console.WriteLine($"CONTRACT topic {topic}: {(pass ? "PASS" : "FAIL")}");
        return pass ? 0 : 1;
    }
    // Test double models the legal dirty-buffer contract; it does not model Shared's policy.
    private sealed class OneBufferPool : ArrayPool<int>
    {
        private readonly int[] buffer = new int[1];
        private bool leased;
        public override int[] Rent(int minimumLength)
        {
            if (minimumLength != 1 || leased) throw new InvalidOperationException();
            leased = true; return buffer;
        }
        public override void Return(int[] array, bool clearArray = false)
        {
            if (!ReferenceEquals(array, buffer) || !leased) throw new InvalidOperationException();
            if (clearArray) Array.Clear(buffer);
            leased = false;
        }
    }
    private sealed class SingleUseSource : IValueTaskSource<int>
    {
        private bool consumed;
        public ValueTask<int> Read() => new(this, 0);
        public int GetResult(short token)
        {
            if (consumed) throw new InvalidOperationException("consumed twice");
            consumed = true; return 1;
        }
        public ValueTaskSourceStatus GetStatus(short token) => ValueTaskSourceStatus.Succeeded;
        public void OnCompleted(Action<object?> continuation, object? state, short token,
                                ValueTaskSourceOnCompletedFlags flags) => continuation(state);
    }
}
