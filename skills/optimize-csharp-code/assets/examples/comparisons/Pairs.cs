using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;

public static class Pairs
{
    public static string BaselineJoin(string[] values)
    {
        string result = "";
        foreach (string value in values)
            result += value;
        return result;
    }

    public static string CandidateJoin(string[] values)
    {
        var result = new StringBuilder();
        foreach (string value in values)
            result.Append(value);
        return result.ToString();
    }

    public static KeyValuePair<string, int>[] BaselineCounts(string[] values)
    {
        var result = new List<KeyValuePair<string, int>>();
        foreach (string value in values)
        {
            int index = result.FindIndex(pair => StringComparer.Ordinal.Equals(pair.Key, value));
            if (index < 0)
                result.Add(new(value, 1));
            else
                result[index] = new(value, result[index].Value + 1);
        }
        return result.ToArray();
    }

    public static KeyValuePair<string, int>[] CandidateCounts(string[] values)
    {
        var indices = new Dictionary<string, int>(StringComparer.Ordinal);
        var result = new List<KeyValuePair<string, int>>();
        foreach (string value in values)
        {
            if (indices.TryGetValue(value, out int index))
                result[index] = new(value, result[index].Value + 1);
            else
            {
                indices.Add(value, result.Count);
                result.Add(new(value, 1));
            }
        }
        return result.ToArray();
    }

    public static bool[] BaselineMembership(string[] values, string[] queries) =>
        queries
            .Select(query =>
                Array.Exists(values, value => StringComparer.Ordinal.Equals(value, query))
            )
            .ToArray();

    public static bool[] CandidateMembership(string[] values, string[] queries)
    {
        var members = new HashSet<string>(values, StringComparer.Ordinal);
        return queries.Select(members.Contains).ToArray();
    }

    public static long BaselineSum(int[] values) =>
        values
            .Where(value => value % 2 == 0)
            .Select(value => checked((long)value * value))
            .ToArray()
            .Sum();

    public static long CandidateSum(ReadOnlySpan<int> values)
    {
        long sum = 0;
        foreach (int value in values)
            if (value % 2 == 0)
                sum = checked(sum + checked((long)value * value));
        return sum;
    }

    public static int BaselineParse(string text, int start, int count) =>
        int.Parse(text.Substring(start, count), NumberStyles.Integer, CultureInfo.InvariantCulture);

    public static int CandidateParse(string text, int start, int count) =>
        int.Parse(text.AsSpan(start, count), NumberStyles.Integer, CultureInfo.InvariantCulture);

    public static int[] BaselineQueue(int[] values)
    {
        var pending = new List<int>(values);
        var result = new List<int>();
        while (pending.Count != 0)
        {
            result.Add(pending[0]);
            pending.RemoveAt(0);
        }
        return result.ToArray();
    }

    public static int[] CandidateQueue(int[] values)
    {
        var pending = new Queue<int>(values);
        var result = new List<int>();
        while (pending.TryDequeue(out int value))
            result.Add(value);
        return result.ToArray();
    }

    public static int[] BaselineDistinct(int[] values)
    {
        var result = new List<int>();
        foreach (int value in values)
            if (!result.Contains(value)) result.Add(value);
        return result.ToArray();
    }

    public static int[] CandidateDistinct(int[] values)
    {
        var seen = new HashSet<int>();
        var result = new List<int>();
        foreach (int value in values)
            if (seen.Add(value)) result.Add(value);
        return result.ToArray();
    }

    public static int BaselineDelimiterCount(string value) => value.Split(':', StringSplitOptions.None).Length - 1;
    public static int CandidateDelimiterCount(string value) => value.Count(character => character == ':');
    public static int[] BaselineReverse(int[] values) => values.Aggregate(new List<int>(), (result, value) => { result.Insert(0, value); return result; }).ToArray();
    public static int[] CandidateReverse(int[] values) => values.Reverse().ToArray();
    public static long[] BaselinePositiveSquares(int[] values) => values.Where(value => value > 0).Select(value => (long)value * value).ToArray();
    public static long[] CandidatePositiveSquares(ReadOnlySpan<int> values)
    {
        var result = new List<long>();
        foreach (int value in values) if (value > 0) result.Add((long)value * value);
        return result.ToArray();
    }

    public static long BaselineBoxedSum(int[] values)
    {
        object[] boxed = values.Cast<object>().ToArray();
        long result = 0;
        foreach (object value in boxed)
            result = checked(result + (int)value);
        return result;
    }

    public static long CandidateSpanSum(ReadOnlySpan<int> values)
    {
        long result = 0;
        foreach (int value in values)
            result = checked(result + value);
        return result;
    }
}
