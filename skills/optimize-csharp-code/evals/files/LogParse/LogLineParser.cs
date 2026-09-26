using System.Globalization;

namespace LogParse;

public enum LogLevel { Debug, Info, Warn, Error }

public readonly record struct LogEntry(long Timestamp, LogLevel Level, int Code);

public static class LogLineParser
{
    // Line format: <unix-seconds>|<LEVEL>|<source>|code=E<number>|<message>
    public static LogEntry Parse(string line)
    {
        string[] parts = line.Split('|');
        if (parts.Length < 4)
            throw new FormatException("expected at least 4 '|'-separated fields");
        long timestamp = long.Parse(parts[0], CultureInfo.InvariantCulture);
        LogLevel level = parts[1] switch
        {
            "DEBUG" => LogLevel.Debug,
            "INFO" => LogLevel.Info,
            "WARN" => LogLevel.Warn,
            "ERROR" => LogLevel.Error,
            _ => throw new FormatException("unknown level: " + parts[1]),
        };
        if (!parts[3].StartsWith("code=E", StringComparison.Ordinal))
            throw new FormatException("missing code field");
        int code = int.Parse(parts[3].Substring(6), CultureInfo.InvariantCulture);
        return new LogEntry(timestamp, level, code);
    }
}
