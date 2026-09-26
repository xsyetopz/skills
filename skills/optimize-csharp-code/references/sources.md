# Sources

Primary documentation behind the cards. Re-check each page for the
target runtime version: several behaviors changed between .NET 8, 9, and
10.

## Runtime and language

| Topic | Source |
| --- | --- |
| .NET 10 JIT: stack allocation, devirtualization, inlining | [What's new in .NET 10 runtime](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-10/runtime) |
| .NET 8 dynamic PGO default | [What's new in .NET 8 runtime](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-8/runtime) |
| C# 14 features, implicit span conversions | [What's new in C# 14](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14) |
| `lock` statement and `System.Threading.Lock` | [lock statement](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/lock) |
| params collections | [Method parameters](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/method-parameters) |
| Compilation settings (tiering, quick JIT, R2R, PGO) | [Compilation config](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation) |
| GC settings (server, DATAS, conserve memory) | [GC config](https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector) |
| Workstation and server GC | [Workstation vs server GC](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/workstation-server-gc) |
| ReadyToRun | [ReadyToRun](https://learn.microsoft.com/en-us/dotnet/core/deploying/ready-to-run) |
| Native AOT | [Native AOT deployment](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/) |
| SIMD | [Use SIMD-accelerated numeric types](https://learn.microsoft.com/en-us/dotnet/standard/simd) |
| Runtime source | [dotnet/runtime](https://github.com/dotnet/runtime) |

## APIs

| Topic | Source |
| --- | --- |
| ArrayPool | [ArrayPool of T](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.arraypool-1) |
| SearchValues | [SearchValues](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.searchvalues) |
| Frozen collections | [System.Collections.Frozen](https://learn.microsoft.com/en-us/dotnet/api/system.collections.frozen) |
| Alternate lookup | [Dictionary.GetAlternateLookup](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.dictionary-2.getalternatelookup) |
| ValueTask | [ValueTask of T](https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.valuetask-1) |
| ValueType equality | [ValueType.Equals](https://learn.microsoft.com/en-us/dotnet/api/system.valuetype.equals) |
| Enum.HasFlag | [Enum.HasFlag](https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag) |
| Regex source generator | [Regex source generators](https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-source-generators) |
| SkipLocalsInit | [SkipLocalsInitAttribute](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.skiplocalsinitattribute) |
| Channels | [System.Threading.Channels](https://learn.microsoft.com/en-us/dotnet/core/extensions/channels) |
| Interlocked | [Interlocked](https://learn.microsoft.com/en-us/dotnet/api/system.threading.interlocked) |
| Allocation per thread | [GC.GetAllocatedBytesForCurrentThread](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread) |
| Pinned object heap | [GC.AllocateArray](https://learn.microsoft.com/en-us/dotnet/api/system.gc.allocatearray) |

## Interop

| Topic | Source |
| --- | --- |
| Best practices | [Native interop best practices](https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices) |
| LibraryImport | [P/Invoke source generation](https://learn.microsoft.com/en-us/dotnet/standard/native-interop/pinvoke-source-generation) |
| UnmanagedCallersOnly | [UnmanagedCallersOnlyAttribute](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.unmanagedcallersonlyattribute) |
| SafeHandle | [SafeHandle](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.safehandle) |
| SDL3 | [SDL3 API](https://wiki.libsdl.org/SDL3/CategoryAPI) |
| BASS | [BASS documentation](https://www.un4seen.com/doc/) |

## Measurement

| Topic | Source |
| --- | --- |
| BenchmarkDotNet overview | [Overview](https://benchmarkdotnet.org/articles/overview.html) |
| BenchmarkDotNet good practices | [Good practices](https://benchmarkdotnet.org/articles/guides/good-practices.html) |
| BenchmarkDotNet console arguments | [Console args](https://benchmarkdotnet.org/articles/guides/console-args.html) |
| BenchmarkDotNet diagnosers | [Diagnosers](https://benchmarkdotnet.org/articles/configs/diagnosers.html) |
| BenchmarkDotNet source | [dotnet/BenchmarkDotNet](https://github.com/dotnet/BenchmarkDotNet) |
| Runtime metrics (.NET 9+) | [Built-in runtime metrics](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/built-in-metrics-runtime) |
| dotnet-counters | [dotnet-counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters) |
| dotnet-trace | [dotnet-trace](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace) |
| Diagnostics tools hub | [.NET diagnostics](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/) |
| Yearly deep dives | [.NET Blog performance posts](https://devblogs.microsoft.com/dotnet/category/performance/) |
