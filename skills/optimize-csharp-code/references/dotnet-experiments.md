# .NET 10 / C# 14 experiments and concrete failure modes

## Resolve the effective build

Inspect `global.json`, project target frameworks, imported props/targets,
`Directory.Build.*`, conditional properties, runtimeconfig and the invocation. A
textual `.csproj` scan cannot resolve these into effective settings. For the
specific project/configuration/framework under test use native MSBuild, for
example:

```sh
dotnet --info
properties=TargetFramework,LangVersion,Optimize,AllowUnsafeBlocks
properties="$properties,RuntimeIdentifier,PublishAot,PublishReadyToRun"
properties="$properties,TieredCompilation,TieredPGO,ServerGarbageCollection"
dotnet msbuild app.csproj -p:Configuration=Release \
  -p:TargetFramework=net10.0 "-getProperty:$properties"
dotnet build app.csproj -c Release -f net10.0 -bl:build.binlog
```

Replace `app.csproj` with the observed project path. Build logs may contain
paths, environment values or credentials; inspect before sharing. Evaluate the
actual configuration rather than switching every project to server GC,
ReadyToRun, NativeAOT or aggressive optimization attributes. These options
answer different startup, memory, deployment and steady-state questions. A
publish setting is not proof that the process was launched with the
corresponding published artifact.

## Locate a cost rather than classify syntax as slow

Use the project's profile first. With provisioned diagnostics tools, collect
runtime counters for the selected PID and trace stacks when those counters
justify it:

```sh
dotnet-counters collect --process-id 1234 --counters System.Runtime \
  --format json --output counters.json
dotnet-trace collect --process-id 1234 --output trace.nettrace
```

PID, permissions, architecture, container namespace and diagnostic socket must
match the target. Observe completion and stop the collectors deliberately.
Counters locate a class of cost; they do not assign it to a function. Methods
named Draw/Update/Parse are candidates for investigation, not measured hot
paths.

## Candidate → missing proof → counterexample

| Candidate | Check before applying | Counterexample |
| --- | --- | --- |
| LINQ → loop/span | Evaluation count/order, exceptions, caller ownership | Materializing a lazy source changes when I/O occurs |
| Pool an array | Outstanding borrowers, reset/clear, return on every path | Returning before an awaited consumer finishes corrupts its input |
| `CollectionsMarshal.AsSpan` | No invalidating list mutation during the view | Add/reallocation leaves a stale view |
| `HasFlag` → bit test | All requested bits, including the zero mask | `(flags & mask) != 0` accepts a partially present multi-bit mask |
| Task → ValueTask | Single consumption and measured synchronous completion | Awaiting a source-backed ValueTask twice violates its contract |
| Reorder/batch rendering | Observable ordering, transparency and state | Texture sorting changes overlapping translucent output |
| Unsafe pointer loop | Bounds, offset overflow, alignment, aliasing and lifetime | A zero-length span has no dereferenceable first element |
| Cached formatted text | Complete key and invalidation on every relevant change | Font/locale/scale change leaves a stale layout |

Equivalent all-bits semantics are `(flags & mask) == mask`, but this is not a
recommendation to replace `HasFlag`: measure the selected runtime's generated
code. Do not label a regex or safety-comment scan as a semantic audit.

C# 14 span conversions and extension members change the language surface; they
do not eliminate the need to inspect overload resolution, enumeration and
lifetime. `field` shortens property implementation, not a blanket performance
improvement.

Use the `.NET` semantic fixture for these invariants and the native
BenchmarkDotNet project for matched timing. Read the interop reference before
changing native resource/callback ownership. Keep correctness tests independent
from baseline/candidate timing and report whole-application pacing separately.

Sources: [msbuild props][upstream-source-1], [evaluate items and
properties][upstream-source-2], [dotnet counters][upstream-source-3], [dotnet
trace][upstream-source-4], [csharp 14][upstream-source-5],
[system.enum.hasflag][upstream-source-6],
[system.threading.tasks.valuetask][upstream-source-7]

[upstream-source-1]: https://learn.microsoft.com/en-us/dotnet/core/project-sdk/msbuild-props
[upstream-source-2]: https://learn.microsoft.com/en-us/visualstudio/msbuild/evaluate-items-and-properties
[upstream-source-3]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters
[upstream-source-4]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace
[upstream-source-5]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14
[upstream-source-6]: https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag
[upstream-source-7]: https://learn.microsoft.com/en-us/dotnet/api/system.threading.tasks.valuetask
