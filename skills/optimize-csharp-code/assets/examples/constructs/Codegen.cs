// Dispatch and code-generation constructs. Verify claims about bounds
// checks, devirtualization, and inlining with DisassemblyDiagnoser output.
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using BenchmarkDotNet.Attributes;

public abstract class Shape
{
    public abstract double Area();
}

public class OpenCircle(double radius) : Shape
{
    public override double Area() => Math.PI * radius * radius;
}

public sealed class SealedCircle(double radius) : Shape
{
    public override double Area() => Math.PI * radius * radius;
}

public static class SealedDispatch
{
    public static double BaselineTotal(OpenCircle[] circles)
    {
        double total = 0;
        foreach (OpenCircle circle in circles)
        {
            total += circle.Area();
        }
        return total;
    }

    // SealedCircle has no overrides, so the JIT can call (and inline)
    // SealedCircle.Area directly instead of through the vtable.
    public static double CandidateTotal(SealedCircle[] circles)
    {
        double total = 0;
        foreach (SealedCircle circle in circles)
        {
            total += circle.Area();
        }
        return total;
    }
}

public static class BoundsChecks
{
    // `count` is unrelated to values.Length, so every values[i] keeps a
    // range check (CORINFO_HELP_RNGCHKFAIL in the disassembly). NoInlining
    // on both methods only keeps each listing standalone for DOTNET_JitDisasm.
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int BaselineSum(int[] values, int count)
    {
        int sum = 0;
        for (int i = 0; i < count; i++)
        {
            sum += values[i];
        }
        return sum;
    }

    // Slicing once proves every index below span.Length; the loop body has
    // no range check and the slice itself validates count once.
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int CandidateSum(int[] values, int count)
    {
        ReadOnlySpan<int> span = values.AsSpan(0, count);
        int sum = 0;
        for (int i = 0; i < span.Length; i++)
        {
            sum += span[i];
        }
        return sum;
    }
}

public static class Vectorization
{
    public static int BaselineCount(ReadOnlySpan<byte> data, byte target)
    {
        int count = 0;
        foreach (byte value in data)
        {
            count += value == target ? 1 : 0;
        }
        return count;
    }

    // Prefer the vectorized BCL primitive when one exists.
    public static int CandidateCountBcl(ReadOnlySpan<byte> data, byte target) => data.Count(target);

    // Hand-written Vector<T> version for operations the BCL lacks.
    public static long CandidateSum(ReadOnlySpan<int> data)
    {
        long total = 0;
        int i = 0;
        if (Vector.IsHardwareAccelerated && data.Length >= Vector<int>.Count)
        {
            var accumulator = Vector<long>.Zero;
            for (; i <= data.Length - Vector<int>.Count; i += Vector<int>.Count)
            {
                var chunk = new Vector<int>(data[i..]);
                Vector.Widen(chunk, out Vector<long> low, out Vector<long> high);
                accumulator += low + high;
            }
            total = Vector.Sum(accumulator);
        }
        for (; i < data.Length; i++)
        {
            total += data[i];
        }
        return total;
    }

    public static long BaselineSum(ReadOnlySpan<int> data)
    {
        long total = 0;
        foreach (int value in data)
        {
            total += value;
        }
        return total;
    }
}

public interface IBinaryOp
{
    int Apply(int left, int right);
}

public readonly struct AddOp : IBinaryOp
{
    public int Apply(int left, int right) => left + right;
}

public static class StructGenerics
{
    public static int BaselineFold(ReadOnlySpan<int> values, Func<int, int, int> op)
    {
        int acc = 0;
        foreach (int value in values)
        {
            acc = op(acc, value);
        }
        return acc;
    }

    // The JIT compiles a separate body per struct TOp, so Apply is a direct,
    // inlinable call; no delegate invocation and no interface dispatch.
    public static int CandidateFold<TOp>(ReadOnlySpan<int> values, TOp op)
        where TOp : struct, IBinaryOp
    {
        int acc = 0;
        foreach (int value in values)
        {
            acc = op.Apply(acc, value);
        }
        return acc;
    }
}

public static class Inlining
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    private static int ClampNoInline(int value, int max) => value > max ? max : value;

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static int ClampInline(int value, int max) => value > max ? max : value;

    public static int BaselineClampAll(ReadOnlySpan<int> values, int max)
    {
        int sum = 0;
        foreach (int value in values)
        {
            sum += ClampNoInline(value, max);
        }
        return sum;
    }

    public static int CandidateClampAll(ReadOnlySpan<int> values, int max)
    {
        int sum = 0;
        foreach (int value in values)
        {
            sum += ClampInline(value, max);
        }
        return sum;
    }
}

public static class LocalsInit
{
    public static int BaselineChecksum(ReadOnlySpan<byte> input)
    {
        Span<byte> scratch = stackalloc byte[1024];
        return Mix(input, scratch);
    }

    // PERF/SAFETY: scratch is fully written by CopyTo before any read of
    // the copied prefix, and Mix only reads scratch[..input.Length].
    [SkipLocalsInit]
    public static int CandidateChecksum(ReadOnlySpan<byte> input)
    {
        Span<byte> scratch = stackalloc byte[1024];
        return Mix(input, scratch);
    }

    private static int Mix(ReadOnlySpan<byte> input, Span<byte> scratch)
    {
        ReadOnlySpan<byte> bounded = input[..Math.Min(input.Length, 1024)];
        bounded.CopyTo(scratch);
        int hash = 0;
        foreach (byte value in scratch[..bounded.Length])
        {
            hash = unchecked(hash * 33 + value);
        }
        return hash;
    }
}

public static partial class RegexUse
{
    public static bool BaselineIsVersion(string text) =>
        new Regex(@"^\d+\.\d+\.\d+$").IsMatch(text);

    [GeneratedRegex(@"^\d+\.\d+\.\d+$", RegexOptions.CultureInvariant)]
    private static partial Regex Version();

    public static bool CandidateIsVersion(string text) => Version().IsMatch(text);
}

[Flags]
public enum Access
{
    None = 0,
    Read = 1,
    Write = 2,
    ReadWrite = Read | Write,
}

public static class FlagTests
{
    // HasFlag(mask) is true only when *all* mask bits are set, and is true
    // for a zero mask. It is a JIT intrinsic (no boxing) on current .NET.
    public static bool HasFlag(Access value, Access mask) => value.HasFlag(mask);

    public static bool AllBits(Access value, Access mask) => (value & mask) == mask;

    // Not equivalent: true when *any* mask bit is set; false for None.
    public static bool AnyBit(Access value, Access mask) => (value & mask) != 0;
}

public static class EnumerableParameter
{
    public static int BaselineSum(IEnumerable<int> values)
    {
        int sum = 0;
        foreach (int value in values)
        {
            sum += value;
        }
        return sum;
    }

    public static int CandidateSum(ReadOnlySpan<int> values)
    {
        int sum = 0;
        foreach (int value in values)
        {
            sum += value;
        }
        return sum;
    }
}

public static class CodegenChecks
{
    public static void Run()
    {
        var open = Enumerable.Range(1, 8).Select(r => new OpenCircle(r)).ToArray();
        var closed = Enumerable.Range(1, 8).Select(r => new SealedCircle(r)).ToArray();
        Check.Equal(
            "sealed",
            SealedDispatch.BaselineTotal(open),
            SealedDispatch.CandidateTotal(closed)
        );

        int[] values = [.. Enumerable.Range(-50, 101)];
        Check.Equal(
            "bounds-checks",
            BoundsChecks.BaselineSum(values, 60),
            BoundsChecks.CandidateSum(values, 60)
        );
        ExpectThrows<IndexOutOfRangeException>(
            "bounds-checks",
            () => BoundsChecks.BaselineSum(values, 102)
        );
        ExpectThrows<ArgumentOutOfRangeException>(
            "bounds-checks",
            () => BoundsChecks.CandidateSum(values, 102)
        );

        byte[] bytes = [.. Enumerable.Range(0, 1000).Select(i => (byte)i)];
        Check.Equal(
            "vectorization",
            Vectorization.BaselineCount(bytes, 7),
            Vectorization.CandidateCountBcl(bytes, 7)
        );
        foreach (int length in new[] { 0, 1, 7, 8, 9, 33, 1000 })
        {
            int[] ints = [.. Enumerable.Range(int.MaxValue - length, length)];
            Check.Equal(
                "vectorization",
                Vectorization.BaselineSum(ints),
                Vectorization.CandidateSum(ints)
            );
        }

        Check.Equal(
            "struct-generic",
            StructGenerics.BaselineFold(values, (a, b) => a + b),
            StructGenerics.CandidateFold(values, new AddOp())
        );
        Check.NoAllocation(
            "struct-generic",
            () => StructGenerics.CandidateFold(values, new AddOp())
        );

        Check.Equal(
            "aggressive-inlining",
            Inlining.BaselineClampAll(values, 10),
            Inlining.CandidateClampAll(values, 10)
        );

        Check.Equal(
            "skiplocalsinit",
            LocalsInit.BaselineChecksum(bytes),
            LocalsInit.CandidateChecksum(bytes)
        );

        foreach (string text in new[] { "1.2.3", "1.2", "10.20.30", "a.b.c" })
        {
            Check.Equal(
                "generated-regex",
                RegexUse.BaselineIsVersion(text),
                RegexUse.CandidateIsVersion(text)
            );
        }
        Check.NoAllocation("generated-regex", () => RegexUse.CandidateIsVersion("1.2.3"));

        foreach (Access value in Enum.GetValues<Access>())
        {
            foreach (Access mask in Enum.GetValues<Access>())
            {
                Check.Equal(
                    "hasflag",
                    FlagTests.HasFlag(value, mask),
                    FlagTests.AllBits(value, mask)
                );
            }
        }
        Check.Equal("hasflag", true, FlagTests.HasFlag(Access.Read, 0));
        Check.Equal("hasflag", false, FlagTests.AnyBit(Access.Read, 0));
        Check.NoAllocation("hasflag", () => FlagTests.HasFlag(Access.Read, Access.Write));

        List<int> list = [.. values];
        Check.Equal(
            "span-parameter",
            EnumerableParameter.BaselineSum(list),
            EnumerableParameter.CandidateSum(
                System.Runtime.InteropServices.CollectionsMarshal.AsSpan(list)
            )
        );
        Check.AllocatesLess(
            "span-parameter",
            () => EnumerableParameter.BaselineSum(list),
            () => EnumerableParameter.CandidateSum(values)
        );
    }

    private static void ExpectThrows<TException>(string construct, Action act)
        where TException : Exception
    {
        try
        {
            act();
        }
        catch (TException)
        {
            Check.Equal(construct, true, true);
            return;
        }
        throw new InvalidOperationException($"{construct}: expected {typeof(TException).Name}");
    }
}

[MemoryDiagnoser]
public class CodegenBenchmarks
{
    private readonly int[] values = [.. Enumerable.Range(0, 4096)];
    private readonly OpenCircle[] open =
    [
        .. Enumerable.Range(1, 1024).Select(r => new OpenCircle(r)),
    ];
    private readonly SealedCircle[] closed =
    [
        .. Enumerable.Range(1, 1024).Select(r => new SealedCircle(r)),
    ];

    [Benchmark(Baseline = true)]
    public int IndexedWithCount() => BoundsChecks.BaselineSum(values, 4096);

    [Benchmark]
    public int SlicedSpan() => BoundsChecks.CandidateSum(values, 4096);

    [Benchmark]
    public long ScalarSum() => Vectorization.BaselineSum(values);

    [Benchmark]
    public long VectorSum() => Vectorization.CandidateSum(values);

    [Benchmark]
    public double OpenDispatch() => SealedDispatch.BaselineTotal(open);

    [Benchmark]
    public double SealedDispatchCall() => SealedDispatch.CandidateTotal(closed);

    [Benchmark]
    public int DelegateFold() => StructGenerics.BaselineFold(values, static (a, b) => a + b);

    [Benchmark]
    public int StructFold() => StructGenerics.CandidateFold(values, new AddOp());
}
