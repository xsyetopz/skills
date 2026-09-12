# .NET measurement and runtime decisions

## Establish the execution contract

Record `dotnet --info`, `global.json`, target frameworks, package resolution,
runtime identifiers, workload and deployment mode. An installed SDK is not proof
of the runtime used by a deployed application. The project's target framework
normally determines the default C# language version; do not force a different
version or use `latest` as a performance fix. [Language selection][language].

Inspect evaluated MSBuild properties, not merely XML elements: imports,
conditions and SDK defaults affect their values. With MSBuild 17.8 or newer:

```sh
dotnet msbuild App.csproj -p:Configuration=Release \
  -getProperty:TargetFramework,LangVersion,Optimize,CheckForOverflowUnderflow
```

For multi-target projects, select the actual framework and relevant runtime
properties for the evaluated build. This inspects evaluation, not the output of
every target or the runtime's final configuration. [MSBuild
evaluation][msbuild].

Preserve checked arithmetic, nullable analysis and diagnostics. Do not import a
blanket performance props file that enables unsafe code, disables overflow
checks or chooses server GC. GC mode depends on process limits and workload;
benchmark the actual deployment before changing it. JIT tiering and dynamic PGO
affect warmup and steady-state behavior. Native AOT and ReadyToRun change
deployment, startup and code-generation tradeoffs; they are not interchangeable
speed flags. [Compilation configuration][compilation], [GC configuration][gc],
[Native AOT][aot].

### RED — DO NOT: apply a blanket performance property set

**Deciding condition:** The requested outcome is lower memory under a
constrained container workload; arithmetic and unsafe-code semantics must not
change.

```xml
<PropertyGroup>
  <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
  <CheckForOverflowUnderflow>false</CheckForOverflowUnderflow>
  <ServerGarbageCollection>true</ServerGarbageCollection>
</PropertyGroup>
```

Why RED:

- the settings change safety and arithmetic semantics without evidence;
- server GC can increase memory and is not universally faster;
- no measured bottleneck connects these properties to the requested outcome.

### GREEN — DO: change one evidenced runtime decision

```text
Constraint: container limit is 256 MiB.
Baseline: server GC peaks at 231 MiB; workstation GC peaks at 142 MiB.
Result: workstation GC meets latency and memory objectives on the deployment
workload, so only ServerGarbageCollection changes.
```

Why GREEN:

- the decision names the deployment constraint and comparable measurements;
- unrelated compiler safety settings remain unchanged;
- latency and memory trade-offs are both tested.

Check:

- publish the same application for the target runtime, repeat the workload under
  the real memory limit, and retain raw counter and latency results.

## Find the limiting path

Use the project's existing profiler where suitable. Runtime counters can locate
allocation, GC, exception or thread-pool symptoms but do not identify the full
causal call path. With compatible installed diagnostic tools, launch an isolated
workload rather than attaching to an unrelated user's process:

```sh
dotnet-counters collect --format json --output counters.json \
  --counters System.Runtime -- dotnet App.dll
dotnet-trace collect --profile dotnet-sampled-thread-time \
  --output thread-time.nettrace -- dotnet App.dll
```

Check installed help and available profiles before adapting these commands. In
tool version 10.0.745401, `dotnet-sampled-thread-time` estimates wall-clock
stack occupancy; `cpu-sampling` belongs to Linux-only `collect-linux`, not the
portable `collect` command. Do not label sampled thread time as CPU utilization.
Ensure the run lasts long enough to emit useful samples and confirm the output
contains the expected workload, not just startup. Diagnostic collection changes
execution overhead; do not use the traced run as the final timing baseline.
[Counters][counters], [tracing][trace].

Separate high CPU from waiting on I/O, contention or thread-pool starvation. A
managed CPU trace does not establish native/GPU costs. For retained-memory
problems inspect roots and lifetimes, not just allocation rate. Bound captures
and handle dumps/traces as potentially sensitive application data.

## Compare equivalent work

Use the existing benchmark suite or [BenchmarkDotNet][bdn] in a separate
benchmark project. Run from that project directory so generated-project
discovery can locate its project file. Build Release without a debugger. Return
or consume the result, prepare representative data outside the timed operation,
and reset mutable state at the appropriate iteration boundary. Compare empty,
typical and large workloads with realistic distributions, not only the easiest
input. Test semantic equivalence separately; a faster incorrect method must not
become the baseline.

Retain warmup, independent measurements and error estimates. Use
`MemoryDiagnoser` for managed allocation evidence. Allocation per operation is
not retained heap size, native memory or peak process memory. Disassembly and
other diagnosers have host/runtime restrictions; confirm support rather than
copying all diagnoser attributes. [Diagnosers][diagnosers].

Match result rows by benchmark, parameters, job and runtime. Missing, failed or
non-numeric measurements are not zero-cost successes. Confirm the expected
benchmarks actually executed; a runner can exit zero after generation failed. Do
not merge distinct parameter rows by method name, compare different runtime jobs
as code-only changes, or strip locale separators without understanding the
exporter format. Keep raw reports and use the benchmark tool's exports rather
than inventing a partial Markdown/CSV parser. A fixed percentage threshold
without noise analysis is not a reliable regression gate.

Finally repeat the application scenario. Report measured scope, variability,
allocation and latency tradeoffs, and untested environments. A startup-only gain
does not prove sustained throughput; a throughput gain does not prove better
p99.

[language]:
  https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/configure-language-version
[msbuild]:
  https://learn.microsoft.com/en-us/visualstudio/msbuild/evaluate-items-and-properties
[compilation]:
  https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation
[gc]:
  https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector
[aot]: https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/
[counters]:
  https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters
[trace]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace
[bdn]: https://benchmarkdotnet.org/articles/guides/getting-started.html
[diagnosers]: https://benchmarkdotnet.org/articles/configs/diagnosers.html
