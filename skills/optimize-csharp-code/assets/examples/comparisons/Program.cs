using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;

public static class Program
{
    private static void Equal<T>(T a, T b)
    {
        if (!EqualityComparer<T>.Default.Equals(a, b))
            throw new InvalidOperationException("expected result mismatch");
    }

    private static void Sequence<T>(IEnumerable<T> a, IEnumerable<T> b)
    {
        if (!a.SequenceEqual(b))
            throw new InvalidOperationException("sequence mismatch");
    }

    private static void Expect<TException>(Action action)
        where TException : Exception
    {
        try
        {
            action();
        }
        catch (TException)
        {
            return;
        }
        throw new InvalidOperationException("expected " + typeof(TException).Name);
    }

    private static void Verify()
    {
        int checks = 0;
        for (int length = 0; length <= 5; length++)
        {
            for (int code = 0; code < (int)Math.Pow(3, length); code++)
            {
                int rest = code;
                int[] values = new int[length];
                for (int i = 0; i < length; i++)
                {
                    values[i] = rest % 3 - 1;
                    rest /= 3;
                }
                int[] saved = (int[])values.Clone();
                string[] strings = values
                    .Select(value => value.ToString(CultureInfo.InvariantCulture))
                    .ToArray();
                Equal(Pairs.BaselineJoin(strings), Pairs.CandidateJoin(strings));
                Sequence(Pairs.BaselineCounts(strings), Pairs.CandidateCounts(strings));
                Sequence(
                    Pairs.BaselineMembership(strings, new[] { "0", "9" }),
                    Pairs.CandidateMembership(strings, new[] { "0", "9" })
                );
                Equal(Pairs.BaselineSum(values), Pairs.CandidateSum(values));
                Equal(Pairs.BaselineBoxedSum(values), Pairs.CandidateSpanSum(values));
                Sequence(Pairs.BaselineQueue(values), Pairs.CandidateQueue(values));
                Sequence(
                    Pairs.BaselinePositiveSquares(values),
                    Pairs.CandidatePositiveSquares(values)
                );
                Sequence(values, saved);
                checks += 8;
            }
        }
        string[] unicode = { "é", "e\u0301", "é", "🙂", "\0" };
        KeyValuePair<string, int>[] expected =
        {
            new("é", 2),
            new("e\u0301", 1),
            new("🙂", 1),
            new("\0", 1),
        };
        Sequence(Pairs.BaselineCounts(unicode), expected);
        Sequence(Pairs.CandidateCounts(unicode), expected);
        Equal(Pairs.BaselineJoin(new[] { "a", "", "é", "🙂" }), "aé🙂");
        Equal(Pairs.CandidateJoin(new[] { "a", "", "é", "🙂" }), "aé🙂");
        Equal(Pairs.BaselineSum(new[] { -3, 2, 2, 0, 5 }), 8L);
        Equal(Pairs.CandidateSum(new[] { -3, 2, 2, 0, 5 }), 8L);
        Sequence(Pairs.BaselineQueue(new[] { 2, 1, 2 }), new[] { 2, 1, 2 });
        Sequence(Pairs.CandidateQueue(new[] { 2, 1, 2 }), new[] { 2, 1, 2 });
        foreach (
            Func<string, int, int, int> parse in new Func<string, int, int, int>[]
            {
                Pairs.BaselineParse,
                Pairs.CandidateParse,
            }
        )
        {
            Equal(parse("x -42 y", 1, 5), -42);
            Equal(parse("2147483647", 0, 10), int.MaxValue);
            Equal(parse("-2147483648", 0, 11), int.MinValue);
            Expect<FormatException>(() => parse("abc", 0, 3));
            Expect<FormatException>(() => parse("", 0, 0));
            Expect<OverflowException>(() => parse("2147483648", 0, 10));
        }
        Expect<OverflowException>(() => Pairs.BaselineSum(new[] { int.MinValue, int.MinValue }));
        Expect<OverflowException>(() => Pairs.CandidateSum(new[] { int.MinValue, int.MinValue }));
        OwnershipTests.Verify();
        Console.WriteLine(
            $"PASS {checks} differential checks + expected results, overflow, pool and flag tests"
        );
    }

    public static void Main(string[] args)
    {
        if (args.Length == 3 && args[0] == "semantics")
        {
            Environment.ExitCode = Semantics.Run(
                args[1],
                int.Parse(args[2], CultureInfo.InvariantCulture)
            );
            return;
        }
        if (args.SequenceEqual(new[] { "verify" }))
        {
            Verify();
            return;
        }
        if (args.Length != 3 || (args[0] != "baseline" && args[0] != "candidate"))
            throw new ArgumentException("usage: Pairs verify | baseline|candidate CASE SIZE");
        int which = int.Parse(args[1], CultureInfo.InvariantCulture);
        int size = int.Parse(args[2], CultureInfo.InvariantCulture);
        if (size < 0 || size > 100000)
            throw new ArgumentOutOfRangeException(nameof(size));
        int[] values = Enumerable.Range(0, size).Select(i => i % 31 - 15).ToArray();
        string[] strings = values
            .Select(value => value.ToString(CultureInfo.InvariantCulture))
            .ToArray();
        bool candidate = args[0] == "candidate";
        object result = which switch
        {
            1 => candidate ? Pairs.CandidateJoin(strings) : Pairs.BaselineJoin(strings),
            2 => candidate ? Pairs.CandidateCounts(strings) : Pairs.BaselineCounts(strings),
            3 => candidate
                ? Pairs.CandidateMembership(strings, strings)
                : Pairs.BaselineMembership(strings, strings),
            4 => candidate ? Pairs.CandidateSum(values) : Pairs.BaselineSum(values),
            5 => strings
                .Select(text =>
                    candidate
                        ? Pairs.CandidateParse(text, 0, text.Length)
                        : Pairs.BaselineParse(text, 0, text.Length)
                )
                .ToArray(),
            6 => candidate ? Pairs.CandidateQueue(values) : Pairs.BaselineQueue(values),
            7 => candidate ? Pairs.CandidateSpanSum(values) : Pairs.BaselineBoxedSum(values),
            8 => candidate
                ? OwnershipTests.PooledChecksum(
                    values.Select(value => (byte)(value + 15)).ToArray()
                )
                : OwnershipTests.AllocateChecksum(
                    values.Select(value => (byte)(value + 15)).ToArray()
                ),
            _ => throw new ArgumentOutOfRangeException(nameof(which)),
        };
        Console.WriteLine(JsonSerializer.Serialize(result, result.GetType()));
    }
}
