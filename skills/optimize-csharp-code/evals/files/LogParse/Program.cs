using System.Diagnostics;
using LogParse;

// Replays a synthetic log through the parser: dotnet run -c Release
var lines = new string[4096];
for (int i = 0; i < lines.Length; i++)
    lines[i] = $"{1_700_000_000 + i}|{(i % 7 == 0 ? "ERROR" : "INFO")}|svc=api-{i % 13}|code=E{i % 600}|request finished in {i % 97} ms";

long checksum = 0;
var sw = Stopwatch.StartNew();
for (int round = 0; round < 500; round++)
    foreach (var line in lines)
    {
        var entry = LogLineParser.Parse(line);
        checksum += entry.Timestamp + entry.Code + (int)entry.Level;
    }
sw.Stop();
Console.WriteLine($"checksum={checksum} elapsed={sw.ElapsedMilliseconds} ms gen0={GC.CollectionCount(0)}");
