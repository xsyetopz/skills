using System.Text;

var mode = args.SingleOrDefault() ?? throw new ArgumentException("usage: benchmark red|green");
var size = int.TryParse(Environment.GetEnvironmentVariable("WORKLOAD_SIZE"), out var parsed)
    ? parsed
    : 20_000;
var values = Enumerable.Range(0, size).Select(index => $"{index % 1000:D4},").ToArray();

string Red(IEnumerable<string> input)
{
    var result = string.Empty;
    foreach (var value in input)
        result += value;
    return result;
}

string Green(IEnumerable<string> input)
{
    var result = new StringBuilder(size * 5);
    foreach (var value in input)
        result.Append(value);
    return result.ToString();
}

var output = mode switch
{
    "red" => Red(values),
    "green" => Green(values),
    _ => throw new ArgumentException("usage: benchmark red|green"),
};
Console.WriteLine($"length={output.Length} checksum={output.Sum(character => character)}");
