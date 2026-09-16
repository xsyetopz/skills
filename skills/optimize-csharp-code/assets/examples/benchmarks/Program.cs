using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

BenchmarkSwitcher.FromAssembly(typeof(DelimiterBench).Assembly).Run(args);

[MemoryDiagnoser]
public class DelimiterBench
{
    [Params(0, 16, 256, 4096)]
    public int Length { get; set; }
    private string text = "";

    [GlobalSetup]
    public void Setup()
    {
        text = new string(Enumerable.Range(0, Length)
            .Select(i => i % 7 == 0 ? ':' : 'x').ToArray());
        int expected = Length == 0 ? 0 : (Length - 1) / 7 + 1;
        if (Split() != expected || Scan() != expected)
            throw new InvalidOperationException("delimiter oracle failed");
    }

    [Benchmark(Baseline = true)]
    public int Split() => text.Split(':').Length - 1;

    [Benchmark]
    public int Scan()
    {
        int count = 0;
        foreach (char character in text.AsSpan())
            if (character == ':') count++;
        return count;
    }
}
