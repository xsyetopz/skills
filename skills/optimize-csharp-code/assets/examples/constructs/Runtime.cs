// Prints the effective runtime configuration of *this process*. Compare the
// output of a build before and after a csproj/runtimeconfig change.
using System.Runtime;
using System.Runtime.CompilerServices;

public static class RuntimeProbe
{
    public static void Print()
    {
        Console.WriteLine($"framework={RuntimeInformationText()}");
        Console.WriteLine($"serverGC={GCSettings.IsServerGC}");
        Console.WriteLine($"latencyMode={GCSettings.LatencyMode}");
        Console.WriteLine($"dynamicCode={RuntimeFeature.IsDynamicCodeSupported}");
        Console.WriteLine($"tieredPGO={Switch("System.Runtime.TieredPGO")}");
        Console.WriteLine($"tieredCompilation={Switch("System.Runtime.TieredCompilation")}");
        Console.WriteLine($"gcDynamicAdaptationMode={Switch("System.GC.DynamicAdaptationMode")}");
        Console.WriteLine($"jittedMethods={System.Runtime.JitInfo.GetCompiledMethodCount()}");
        Console.WriteLine(
            $"jitTimeMs={System.Runtime.JitInfo.GetCompilationTime().TotalMilliseconds:F1}"
        );
        Console.WriteLine(
            $"vectorHardware={System.Numerics.Vector.IsHardwareAccelerated}"
                + $" vectorBits={System.Numerics.Vector<byte>.Count * 8}"
        );
    }

    private static string RuntimeInformationText() =>
        System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription;

    // AppContext only reports switches that were set explicitly in
    // runtimeconfig.json or by an MSBuild property; "unset" means default.
    private static string Switch(string name) => AppContext.GetData(name)?.ToString() ?? "unset";
}
