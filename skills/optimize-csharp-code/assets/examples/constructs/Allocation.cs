// Allocation constructs. Each pair keeps Baseline and Candidate observably
// equivalent; AllocationChecks.Run proves equivalence and the allocation claim.
using System.Buffers;
using System.Collections.Concurrent;
using System.Collections.Frozen;
using System.Runtime.InteropServices;
using System.Text;
using BenchmarkDotNet.Attributes;

public static class SpanParsing
{
    // Input shape: "12;7;-3". Empty fields are rejected by int.Parse in both.
    public static int BaselineSum(string csv)
    {
        int sum = 0;
        foreach (string field in csv.Split(';'))
        {
            sum += int.Parse(field.Trim());
        }
        return sum;
    }

    public static int CandidateSum(ReadOnlySpan<char> csv)
    {
        int sum = 0;
        foreach (Range range in csv.Split(';'))
        {
            sum += int.Parse(csv[range].Trim());
        }
        return sum;
    }
}

public static class Utf8Checksum
{
    private const int StackLimitBytes = 256;

    public static int Baseline(string text)
    {
        byte[] bytes = Encoding.UTF8.GetBytes(text);
        return Fold(bytes);
    }

    public static int Candidate(string text)
    {
        int maxBytes = Encoding.UTF8.GetMaxByteCount(text.Length);
        byte[]? rented = null;
        // PERF/SAFETY: stackalloc is bounded by StackLimitBytes; larger
        // inputs rent from the shared pool and are returned in finally.
        Span<byte> buffer =
            maxBytes <= StackLimitBytes
                ? stackalloc byte[StackLimitBytes]
                : (rented = ArrayPool<byte>.Shared.Rent(maxBytes));
        try
        {
            int written = Encoding.UTF8.GetBytes(text, buffer);
            return Fold(buffer[..written]);
        }
        finally
        {
            if (rented is not null)
            {
                ArrayPool<byte>.Shared.Return(rented);
            }
        }
    }

    private static int Fold(ReadOnlySpan<byte> bytes)
    {
        int hash = 17;
        foreach (byte value in bytes)
        {
            hash = unchecked(hash * 31 + value);
        }
        return hash;
    }
}

public static class StringCreation
{
    public static string BaselineReverse(string text) => new string(text.Reverse().ToArray());

    public static string CandidateReverse(string text) =>
        string.Create(
            text.Length,
            text,
            static (span, source) =>
            {
                source.AsSpan().CopyTo(span);
                span.Reverse();
            }
        );
}

public static class SpanFormatting
{
    public static string BaselinePoint(int x, int y) => string.Format("({0}, {1})", x, y);

    // Writes into caller storage; returns chars written or -1 when too small.
    public static int CandidatePoint(Span<char> destination, int x, int y) =>
        destination.TryWrite($"({x}, {y})", out int written) ? written : -1;
}

public static class Joining
{
    public static string BaselineJoin(string[] parts)
    {
        string result = "";
        foreach (string part in parts)
        {
            result += part;
        }
        return result;
    }

    public static string CandidateJoin(string[] parts)
    {
        int length = 0;
        foreach (string part in parts)
        {
            length += part.Length;
        }
        var builder = new StringBuilder(length);
        foreach (string part in parts)
        {
            builder.Append(part);
        }
        return builder.ToString();
    }
}

public static class ClosureAvoidance
{
    public static int BaselineGetOrAdd(ConcurrentDictionary<int, int> cache, int key, int offset) =>
        cache.GetOrAdd(key, k => k + offset);

    public static int CandidateGetOrAdd(
        ConcurrentDictionary<int, int> cache,
        int key,
        int offset
    ) => cache.GetOrAdd(key, static (k, extra) => k + extra, offset);
}

public readonly struct PlainKey(int a, int b)
{
    public int A { get; } = a;
    public int B { get; } = b;
}

public readonly struct EquatableKey(int a, int b) : IEquatable<EquatableKey>
{
    public int A { get; } = a;
    public int B { get; } = b;

    public bool Equals(EquatableKey other) => A == other.A && B == other.B;

    public override bool Equals(object? obj) => obj is EquatableKey other && Equals(other);

    public override int GetHashCode() => HashCode.Combine(A, B);
}

public static class LinqToLoop
{
    public static long BaselineEvenSquares(int[] values) =>
        values.Where(v => v % 2 == 0).Select(v => (long)v * v).Sum();

    public static long CandidateEvenSquares(ReadOnlySpan<int> values)
    {
        long sum = 0;
        foreach (int value in values)
        {
            if (value % 2 == 0)
            {
                sum = checked(sum + (long)value * value);
            }
        }
        return sum;
    }
}

public static class Presizing
{
    public static List<int> BaselineSquares(int count)
    {
        var list = new List<int>();
        for (int i = 0; i < count; i++)
        {
            list.Add(i * i);
        }
        return list;
    }

    public static List<int> CandidateSquares(int count)
    {
        var list = new List<int>(count);
        for (int i = 0; i < count; i++)
        {
            list.Add(i * i);
        }
        return list;
    }
}

public static class RefDictionary
{
    public static void BaselineCount(Dictionary<string, int> counts, string key)
    {
        counts.TryGetValue(key, out int current);
        counts[key] = current + 1;
    }

    public static void CandidateCount(Dictionary<string, int> counts, string key)
    {
        // PERF/SAFETY: the ref is used before any other mutation of counts.
        ref int slot = ref CollectionsMarshal.GetValueRefOrAddDefault(counts, key, out _);
        slot++;
    }

    public static int BaselineSumList(List<int> values)
    {
        int sum = 0;
        foreach (int value in values)
        {
            sum += value;
        }
        return sum;
    }

    public static int CandidateSumList(List<int> values)
    {
        int sum = 0;
        // PERF/SAFETY: values is not resized while the span is alive.
        foreach (int value in CollectionsMarshal.AsSpan(values))
        {
            sum += value;
        }
        return sum;
    }
}

public sealed class ValueTaskCache
{
    private readonly Dictionary<int, int> cache = [];

    public async Task<int> BaselineGetAsync(int key)
    {
        if (cache.TryGetValue(key, out int hit))
        {
            return hit;
        }
        await Task.Yield();
        return cache[key] = key * 1000;
    }

    public ValueTask<int> CandidateGetAsync(int key)
    {
        if (cache.TryGetValue(key, out int hit))
        {
            return new ValueTask<int>(hit);
        }
        return new ValueTask<int>(LoadAsync(key));
    }

    private async Task<int> LoadAsync(int key)
    {
        await Task.Yield();
        return cache[key] = key * 1000;
    }
}

public static class SearchValuesUse
{
    private static readonly char[] ForbiddenArray = "<>:\"/\\|?*\0\t\r\n".ToCharArray();

    private static readonly SearchValues<char> Forbidden = SearchValues.Create(
        "<>:\"/\\|?*\0\t\r\n"
    );

    public static int BaselineFirstInvalid(string name) => name.IndexOfAny(ForbiddenArray);

    public static int CandidateFirstInvalid(ReadOnlySpan<char> name) => name.IndexOfAny(Forbidden);
}

public static class FrozenLookup
{
    private static readonly string[] Keywords =
    [
        "abstract",
        "base",
        "class",
        "delegate",
        "event",
        "fixed",
        "goto",
        "implicit",
        "interface",
        "namespace",
        "operator",
        "sealed",
        "stackalloc",
        "unsafe",
        "volatile",
        "while",
    ];

    private static readonly HashSet<string> Mutable = new(Keywords, StringComparer.Ordinal);

    private static readonly FrozenSet<string> Frozen = Keywords.ToFrozenSet(StringComparer.Ordinal);

    public static int BaselineCount(string[] words)
    {
        int hits = 0;
        foreach (string word in words)
        {
            hits += Mutable.Contains(word) ? 1 : 0;
        }
        return hits;
    }

    public static int CandidateCount(string[] words)
    {
        int hits = 0;
        foreach (string word in words)
        {
            hits += Frozen.Contains(word) ? 1 : 0;
        }
        return hits;
    }
}

public static class AlternateLookup
{
    public static void BaselineCountWords(Dictionary<string, int> counts, string text)
    {
        foreach (string word in text.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            counts[word] = counts.GetValueOrDefault(word) + 1;
        }
    }

    // counts must use StringComparer.Ordinal (or another comparer that
    // implements IAlternateEqualityComparer<ReadOnlySpan<char>, string>).
    public static void CandidateCountWords(Dictionary<string, int> counts, ReadOnlySpan<char> text)
    {
        var lookup = counts.GetAlternateLookup<ReadOnlySpan<char>>();
        foreach (Range range in text.Split(' '))
        {
            ReadOnlySpan<char> word = text[range];
            if (word.IsEmpty)
            {
                continue;
            }
            lookup[word] = lookup.TryGetValue(word, out int n) ? n + 1 : 1;
        }
    }
}

public static class ParamsSpan
{
    public static int BaselineMax(params int[] values)
    {
        int max = int.MinValue;
        foreach (int value in values)
        {
            max = Math.Max(max, value);
        }
        return max;
    }

    public static int CandidateMax(params ReadOnlySpan<int> values)
    {
        int max = int.MinValue;
        foreach (int value in values)
        {
            max = Math.Max(max, value);
        }
        return max;
    }
}

public static class JitStackAllocation
{
    // .NET 10 escape analysis: the array never leaves the method, so the
    // optimizing JIT may place it on the stack instead of the heap.
    public static int SumOfThree()
    {
        int[] numbers = { 1, 2, 3 };
        int sum = 0;
        for (int i = 0; i < numbers.Length; i++)
        {
            sum += numbers[i];
        }
        return sum;
    }
}

public static class AllocationChecks
{
    public static void Run()
    {
        const string csv = "12; 7;-3;40";
        Check.Equal("span-parsing", SpanParsing.BaselineSum(csv), SpanParsing.CandidateSum(csv));
        Check.NoAllocation("span-parsing", () => SpanParsing.CandidateSum(csv));

        foreach (string text in new[] { "", "héllo", new string('x', 1000) })
        {
            Check.Equal(
                "stackalloc-pool",
                Utf8Checksum.Baseline(text),
                Utf8Checksum.Candidate(text)
            );
        }
        Check.NoAllocation("stackalloc-pool", () => Utf8Checksum.Candidate("short input"));
        string large = new('y', 4000);
        Check.NoAllocation("stackalloc-pool", () => Utf8Checksum.Candidate(large));

        Check.Equal(
            "string-create",
            StringCreation.BaselineReverse("abcé"),
            StringCreation.CandidateReverse("abcé")
        );
        Check.AllocatesLess(
            "string-create",
            () => StringCreation.BaselineReverse("abcdefghij"),
            () => StringCreation.CandidateReverse("abcdefghij")
        );

        Span<char> buffer = stackalloc char[32];
        int written = SpanFormatting.CandidatePoint(buffer, -4, 12);
        Check.Equal(
            "span-formatting",
            SpanFormatting.BaselinePoint(-4, 12),
            new string(buffer[..written])
        );
        Check.Equal("span-formatting", -1, SpanFormatting.CandidatePoint(stackalloc char[3], 1, 2));
        char[] heapBuffer = new char[32];
        Check.NoAllocation(
            "span-formatting",
            () => SpanFormatting.CandidatePoint(heapBuffer, 1, 2)
        );

        string[] parts = Enumerable.Range(0, 64).Select(i => $"p{i}").ToArray();
        Check.Equal("stringbuilder", Joining.BaselineJoin(parts), Joining.CandidateJoin(parts));
        Check.AllocatesLess(
            "stringbuilder",
            () => Joining.BaselineJoin(parts),
            () => Joining.CandidateJoin(parts)
        );

        var cache = new ConcurrentDictionary<int, int>();
        Check.Equal(
            "static-lambda",
            ClosureAvoidance.BaselineGetOrAdd(new(), 3, 4),
            ClosureAvoidance.CandidateGetOrAdd(cache, 3, 4)
        );
        Check.NoAllocation("static-lambda", () => ClosureAvoidance.CandidateGetOrAdd(cache, 3, 4));

        var plain = new Dictionary<PlainKey, int> { [new(1, 2)] = 5 };
        var equatable = new Dictionary<EquatableKey, int> { [new(1, 2)] = 5 };
        Check.Equal("iequatable-key", plain[new(1, 2)], equatable[new(1, 2)]);
        Check.AllocatesLess(
            "iequatable-key",
            () => _ = plain[new(1, 2)],
            () => _ = equatable[new(1, 2)]
        );
        Check.NoAllocation("iequatable-key", () => _ = equatable[new(1, 2)]);

        int[] numbers = [1, 2, 3, 4, -6, int.MaxValue - 1];
        Check.Equal(
            "linq-to-loop",
            LinqToLoop.BaselineEvenSquares(numbers),
            LinqToLoop.CandidateEvenSquares(numbers)
        );
        Check.NoAllocation("linq-to-loop", () => LinqToLoop.CandidateEvenSquares(numbers));

        Check.SequenceEqual(
            "presize",
            Presizing.BaselineSquares(1000),
            Presizing.CandidateSquares(1000)
        );
        Check.AllocatesLess(
            "presize",
            () => Presizing.BaselineSquares(1000),
            () => Presizing.CandidateSquares(1000)
        );

        var left = new Dictionary<string, int>(StringComparer.Ordinal);
        var right = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (string key in new[] { "a", "b", "a", "c", "a" })
        {
            RefDictionary.BaselineCount(left, key);
            RefDictionary.CandidateCount(right, key);
        }
        Check.SequenceEqual(
            "collectionsmarshal",
            left.OrderBy(p => p.Key),
            right.OrderBy(p => p.Key)
        );
        List<int> list = [.. Enumerable.Range(0, 100)];
        Check.Equal(
            "collectionsmarshal",
            RefDictionary.BaselineSumList(list),
            RefDictionary.CandidateSumList(list)
        );
        Check.NoAllocation("collectionsmarshal", () => RefDictionary.CandidateCount(right, "a"));

        var baselineCache = new ValueTaskCache();
        var candidateCache = new ValueTaskCache();
        Check.Equal(
            "valuetask",
            baselineCache.BaselineGetAsync(42).GetAwaiter().GetResult(),
            candidateCache.CandidateGetAsync(42).AsTask().GetAwaiter().GetResult()
        );
        Check.AllocatesLess(
            "valuetask",
            () => baselineCache.BaselineGetAsync(42).GetAwaiter().GetResult(),
            () => candidateCache.CandidateGetAsync(42).GetAwaiter().GetResult()
        );

        foreach (string name in new[] { "ok.txt", "bad|name", "", "tab\tx" })
        {
            Check.Equal(
                "searchvalues",
                SearchValuesUse.BaselineFirstInvalid(name),
                SearchValuesUse.CandidateFirstInvalid(name)
            );
        }

        string[] words = ["class", "Class", "while", "foo", "", "sealed"];
        Check.Equal(
            "frozen-collections",
            FrozenLookup.BaselineCount(words),
            FrozenLookup.CandidateCount(words)
        );

        const string sentence = "to be  or not to be";
        var byString = new Dictionary<string, int>(StringComparer.Ordinal);
        var bySpan = new Dictionary<string, int>(StringComparer.Ordinal);
        AlternateLookup.BaselineCountWords(byString, sentence);
        AlternateLookup.CandidateCountWords(bySpan, sentence);
        Check.SequenceEqual(
            "alternate-lookup",
            byString.OrderBy(p => p.Key),
            bySpan.OrderBy(p => p.Key)
        );
        Check.NoAllocation(
            "alternate-lookup",
            () => AlternateLookup.CandidateCountWords(bySpan, sentence)
        );

        Check.Equal("jit-stack-allocation", 6, JitStackAllocation.SumOfThree());
        Check.NoAllocation("jit-stack-allocation", () => JitStackAllocation.SumOfThree());

        Check.Equal(
            "params-span",
            ParamsSpan.BaselineMax(3, 9, -1),
            ParamsSpan.CandidateMax(3, 9, -1)
        );
        Check.NoAllocation("params-span", () => ParamsSpan.CandidateMax(3, 9, -1));
    }
}

[MemoryDiagnoser]
public class AllocationBenchmarks
{
    private const string Csv = "12;7;-3;40;18;99;-100;5";
    private readonly string[] parts = Enumerable.Range(0, 64).Select(i => $"p{i}").ToArray();
    private readonly Dictionary<PlainKey, int> plain = new() { [new(1, 2)] = 5 };
    private readonly Dictionary<EquatableKey, int> equatable = new() { [new(1, 2)] = 5 };

    [Benchmark(Baseline = true)]
    public int SplitParse() => SpanParsing.BaselineSum(Csv);

    [Benchmark]
    public int SpanParse() => SpanParsing.CandidateSum(Csv);

    [Benchmark]
    public string ConcatJoin() => Joining.BaselineJoin(parts);

    [Benchmark]
    public string BuilderJoin() => Joining.CandidateJoin(parts);

    [Benchmark]
    public int PlainStructKey() => plain[new(1, 2)];

    [Benchmark]
    public int EquatableStructKey() => equatable[new(1, 2)];
}
