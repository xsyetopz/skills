using System;
using System.Globalization;

if (args.Length != 0)
    throw new ArgumentException();
CultureInfo.CurrentCulture = new CultureInfo("tr-TR");
bool actual = string.Equals("FILE", "file", StringComparison.CurrentCultureIgnoreCase);
bool expected = string.Equals("FILE", "file", StringComparison.OrdinalIgnoreCase);
Console.WriteLine($"actual={actual} expected ordinal={expected}");
if (actual == expected)
    Environment.Exit(1);
