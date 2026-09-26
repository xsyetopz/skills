// Usage:
//   dotnet run -c Release -- verify        equivalence + allocation oracles
//   dotnet run -c Release -- runtime       effective runtime configuration
//   dotnet run -c Release -- bench [BDN]   BenchmarkDotNet (e.g. --job short)
using BenchmarkDotNet.Running;

switch (args.FirstOrDefault())
{
    case "verify":
        AllocationChecks.Run();
        CodegenChecks.Run();
        ConcurrencyChecks.Run();
        InteropChecks.Run();
        Console.WriteLine($"VERIFY PASSED: {Check.Count} checks");
        return 0;
    case "runtime":
        RuntimeProbe.Print();
        return 0;
    case "bench":
        LibC.Register();
        BenchmarkSwitcher.FromAssembly(typeof(Check).Assembly).Run(args[1..]);
        return 0;
    default:
        Console.Error.WriteLine("usage: Constructs verify|runtime|bench ...");
        return 2;
}
