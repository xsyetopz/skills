# Runtime configuration constructs

These settings change how the whole process compiles code and collects
garbage. Set each through an MSBuild property (written into
`<app>.runtimeconfig.json`), a `runtimeconfig.template.json` entry, or a
`DOTNET_` environment variable. Environment variables take hexadecimal
numbers; JSON takes decimal
([GC config][gc-config],
[compilation config][compilation-config]).

The probe `sh assets/examples/verify.sh runtime` prints what the running
process uses (`GCSettings.IsServerGC`, `RuntimeFeature`,
`JitInfo.GetCompiledMethodCount()`, and explicitly set `AppContext`
switches). Run it, or the same lines in the app, before and after every
change: a property in a `.csproj` does not prove the deployed process
runs with it.

## Contents

- Tiered compilation and quick JIT
- Tiered PGO
- ReadyToRun
- Native AOT
- Server GC
- DATAS
- Conserve memory

## Tiered compilation and quick JIT

**Definition.** With tiered compilation (default on since .NET Core 3.0),
methods first run as quickly compiled unoptimized code (tier 0) or
ReadyToRun code, and the runtime recompiles hot methods optimized in the
background. `TieredCompilation=false` compiles everything fully optimized
on first call. `TieredCompilationQuickJit=false` makes methods without
ReadyToRun code compile optimized immediately.

**Use when.**

- Allocation or timing assertions in tests must reflect optimized code:
  set `DOTNET_TieredCompilation=0` for that test process only. Measured:
  a `TryWrite` call allocated 48 B at tier 0 and 0 B optimized.
- A latency-critical service shows early-request slowness from tier-0
  code, and startup time is not a constraint (measure both).

**Do not use when.**

- Startup time matters: disabling tiering compiles every method fully
  optimized on first call.
- Making it a global production default without measurement: disabling
  tiering also disables tiered PGO.

**Example.**

```xml
<PropertyGroup>
  <TieredCompilation>false</TieredCompilation>
</PropertyGroup>
```

```sh
DOTNET_TieredCompilation=0 dotnet bin/Release/net10.0/App.dll
```

The documentation says quick JIT for loops is off when the setting is
omitted, while .NET 7 enabled it by default together with on-stack
replacement. Treat the current default as unconfirmed: read it from the
probe or a trace instead of assuming either.

**Cost removed.** Tier-0 execution of hot methods before tier-up. Compare
`jittedMethods` and `jitTimeMs` from the probe and the latency of the first
N requests.

**Verify.**

1. `sh verify.sh runtime` with and without the variable: the probe prints
   `tieredCompilation=False` only when set via runtimeconfig; with the
   environment variable, confirm through `DOTNET_JitDisasm` headers, which
   show `(FullOpts)` instead of `(Tier0)`.
1. Measure startup and warm latency separately.

## Tiered PGO

**Definition.** Dynamic profile-guided optimization instruments tier-0
code, then uses the observed types, branches, and call targets when
compiling tier-1 code (guarded devirtualization, hot/cold layout). It has
been on by default since .NET 8
([.NET 8 runtime][net-8-runtime]);
`TieredPGO=false` or `DOTNET_TieredPGO=0` disables it.

**Use when.**

- Leave it on. Use `DOTNET_TieredPGO=0` only as a diagnostic: a benchmark
  with and without PGO shows how much of a construct's benefit PGO
  already provides (see the sealed and struct-generic cards in
  [codegen](codegen.md)).

**Do not use when.**

- Disabling it for production "predictability" without a measurement.

**Example.**

```sh
DOTNET_TieredPGO=0 dotnet bin/Release/net10.0/App.dll
```

**Cost removed.** Virtual/delegate dispatch and poor code layout on hot
paths, automatically. Compare steady-state benchmark means with PGO on
and off.

**Verify.**

1. Run the benchmark twice, the second time with `DOTNET_TieredPGO=0` in
   the environment of the benchmark process
   (`--envVars DOTNET_TieredPGO:0` in BenchmarkDotNet).
1. Report both. A construct whose gain appears only with PGO off helps
   only where PGO does not run (NativeAOT, cold code).

## ReadyToRun

**Definition.** `PublishReadyToRun=true` precompiles the app's IL to native
code at publish time (per runtime identifier). The JIT still runs for code
it cannot use precompiled and for tier-1 re-optimization of hot methods
([ReadyToRun]).

**Use when.**

- Startup or first-request latency is the metric and the app's own code is
  a meaningful part of what gets JIT-compiled at startup.

**Do not use when.**

- Deployment must be architecture-neutral (R2R binaries are
  RID-specific), or binary size is constrained (R2R assemblies are
  larger).
- The metric is steady-state throughput: tiering recompiles hot code
  anyway.

**Example.**

```sh
dotnet publish -c Release -r osx-arm64 -p:PublishReadyToRun=true -o out
./out/App
```

**Cost removed.** JIT work at startup. Measured probe, example project:
`jittedMethods=16` for the normal build versus `jittedMethods=5` for the
ReadyToRun publish, at the point the probe runs (the framework itself is
already ReadyToRun in both).

**Verify.**

1. Probe: `JitInfo.GetCompiledMethodCount()` drops at the same point in
   startup.
1. Startup time: `hyperfine -N --warmup 3 './out/App' 'dotnet
   bin/Release/net10.0/App.dll'` with identical arguments.

## Native AOT

**Definition.** `PublishAot=true` compiles the app and its dependencies to
a single native executable with no JIT at run time. Unreferenced code is
trimmed, and dynamic code generation is unavailable
(`RuntimeFeature.IsDynamicCodeSupported == false`)
([Native AOT deployment][native-aot-deployment]).

**Use when.**

- Startup time and memory footprint dominate (CLI tools, serverless,
  containers scaled to zero) and all dependencies are trim- and
  AOT-compatible.

**Do not use when.**

- The app uses reflection emit, dynamic assembly loading, or libraries
  that produce trim/AOT warnings. Measured: publishing the example project
  with `PublishAot` failed with `IL2104` (BenchmarkDotNet,
  CommandLineParser) and `IL3000` errors, because warnings are errors
  there. These are real incompatibilities, not noise.
- Steady-state peak throughput is the goal: there is no tier-1
  re-optimization or dynamic PGO.

**Example.**

```xml
<PropertyGroup>
  <PublishAot>true</PublishAot>
</PropertyGroup>
```

```sh
dotnet publish -c Release -r linux-x64 -o out
./out/App
```

**Cost removed.** JIT startup and the runtime's JIT/IL memory. Measure
startup with `hyperfine` and peak RSS with `/usr/bin/time -l` (macOS) or
`/usr/bin/time -v` (Linux).

**Verify.**

1. Publish with zero trim/AOT warnings (`IL2xxx`, `IL3xxx`).
1. The probe prints `dynamicCode=False`.
1. Run the full test suite against the published binary, not the JIT
   build.

Verification tier: **not runnable here**. The Homebrew .NET SDK 10.0.400 on
the test machine failed the native link step (`MSB3073` from `clang`) for
a minimal project. The commands above are the documented flow and were
not executed.

## Server GC

**Definition.** Server GC (`ServerGarbageCollection=true`,
`System.GC.Server`, `DOTNET_gcServer=1`) uses one heap and one dedicated GC
thread per logical CPU (subject to limits) for higher throughput at the
cost of memory. Workstation GC is the runtime default; ASP.NET Core apps
(`Microsoft.NET.Sdk.Web`) default to server GC
([workstation vs server GC][workstation-vs-server-gc]).

**Use when.**

- GC limits a multi-core server's throughput (`dotnet.gc.pause.time`
  grows fast relative to wall time, many gen0 collections), and the
  server has memory headroom.

**Do not use when.**

- Many processes share one machine or container memory is tight: per-core
  heaps multiply the footprint (DATAS, next card, mitigates this on .NET
  9+).

**Example.**

```xml
<PropertyGroup>
  <ServerGarbageCollection>true</ServerGarbageCollection>
</PropertyGroup>
```

**Cost removed.** GC pause time per allocated byte on multi-core
throughput workloads. Watch `dotnet.gc.pause.time`, `dotnet.gc.collections`
(`gen0`), and `dotnet.gc.last_collection.heap.size` in
`dotnet-counters monitor --counters System.Runtime`, plus the throughput
metric.

**Verify.**

1. The probe prints `serverGC=True` (confirmed with
   `DOTNET_gcServer=1`).
1. Compare throughput, p99 latency, and working set under the production
   load with both settings.

## DATAS

**Definition.** Dynamic adaptation to application sizes
(`GarbageCollectionAdaptationMode`, `System.GC.DynamicAdaptationMode`,
`DOTNET_GCDynamicAdaptationMode`) lets server GC start with one heap and
grow or shrink the heap count so the heap size tracks the live data size.
It applies to server GC and is enabled by default starting in .NET 9
([DATAS]).

**Use when.**

- Server GC runs in containers or bursty services where memory should
  follow load. Leave the default on.

**Do not use when.**

- A latency-critical service cannot absorb allocation waits while DATAS
  adds heaps after a load step (the docs describe these transient waits).
  Test a load ramp, and set `0` only if the ramp shows them.

**Example.**

```xml
<PropertyGroup>
  <ServerGarbageCollection>true</ServerGarbageCollection>
  <GarbageCollectionAdaptationMode>0</GarbageCollectionAdaptationMode>
</PropertyGroup>
```

(`0` disables; omit the property to keep the .NET 9+ default.)

**Cost removed.** Excess committed memory from per-core heaps when load is
low. Watch `dotnet.gc.last_collection.heap.size` and
`dotnet.process.memory.working_set` at idle and at peak.

**Verify.**

1. The probe prints `gcDynamicAdaptationMode=0` when set explicitly.
1. Load ramp test: heap size and p99 latency across the ramp.

## Conserve memory

**Definition.** `System.GC.ConserveMemory` / `DOTNET_GCConserveMemory`
(0-9, .NET 6+) makes the GC trade more frequent collections and longer
pauses for a smaller heap. Any non-zero value also compacts a fragmented
large object heap automatically. The docs suggest starting between 5 and
7.

**Use when.**

- Memory is the constraint (container limit, density) and the service can
  absorb more GC time.

**Do not use when.**

- Latency or throughput is the constraint.

**Example.**

```json
{
  "configProperties": {
    "System.GC.ConserveMemory": 5
  }
}
```

(in `runtimeconfig.template.json`; there is no dedicated MSBuild property,
so use a `RuntimeHostConfigurationOption` item or the template file).

**Cost removed.** Heap growth and LOH fragmentation. Watch
`dotnet.gc.last_collection.heap.size`,
`dotnet.gc.last_collection.heap.fragmentation.size`, and
`dotnet.gc.pause.time`.

**Verify.**

1. `GC.GetConfigurationVariables()` in the process lists the effective
   `GCConserveMemory` value.
1. Compare heap size and GC time under the same load.

[gc-config]: https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector
[compilation-config]: https://learn.microsoft.com/en-us/dotnet/core/runtime-config/compilation
[net-8-runtime]: https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-8/runtime#performance-improvements
[readytorun]: https://learn.microsoft.com/en-us/dotnet/core/deploying/ready-to-run
[native-aot-deployment]: https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/
[workstation-vs-server-gc]: https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/workstation-server-gc
[datas]: https://learn.microsoft.com/en-us/dotnet/core/runtime-config/garbage-collector#dynamic-adaptation-to-application-sizes-datas
