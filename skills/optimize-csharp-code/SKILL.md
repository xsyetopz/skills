---
name: optimize-csharp-code
description: >-
  Profiles and optimizes C#/.NET CPU time, latency, and allocations with
  BenchmarkDotNet, dotnet-counters, dotnet-trace, and JIT disassembly. Use
  when a .NET benchmark or profile shows the cost. Not for framework upgrades
  alone.
---

# Optimize C# Code

Make a measured .NET hot path cheaper without changing observable behavior.
Each change applies one reference card to a cost that a profile attributes,
is checked by an equivalence oracle, and is kept only if the metric the
card names improves. The cards record preconditions, semantic traps, and
exact verification steps, so read the card before applying a construct.

## Workflow

1. Record the target: read `global.json`, the `.csproj` and
   `Directory.Build.*`, then print evaluated settings with
   `dotnet msbuild <project> -getProperty:TargetFramework,LangVersion,`
   `Optimize,TieredPGO,ServerGarbageCollection,PublishAot` (one argument;
   see [measurement](references/measurement.md#effective-msbuild-properties)).
   Keep the project's framework and language version; do not upgrade them
   to reach a construct unless the user asked.
1. Reproduce the workload in Release without a debugger. Pick the metric the
   user cares about: mean latency, tail latency, throughput, allocated
   bytes per operation, GC pause, working set, or startup.
1. Attribute the cost before editing:
   - allocation or GC symptoms: `dotnet-counters monitor` (`System.Runtime`),
     then an allocation trace;
   - CPU symptoms: `dotnet-trace collect` with the CPU sampling profile;
   - one isolated method: a BenchmarkDotNet class with `[MemoryDiagnoser]`.
   Commands are in [measurement](references/measurement.md).
1. Choose one construct from the routing table whose **Use when**
   matches the evidence and whose **Do not use when** does not.
1. Write or extend the oracle first: baseline and candidate on the same
   inputs, including empty, boundary, overflow, and error cases. Use the
   project's test framework; `Check.cs` in the examples shows the minimum.
1. Apply the change. Give every `unsafe`, `stackalloc`, `CollectionsMarshal`
   (spans over lists), `MemoryMarshal`, pooling, pinning, and
   `SkipLocalsInit` use a `// PERF/SAFETY:` comment that states the
   invariant (bound, lifetime, no concurrent mutation).
1. Verify with the card's **Verify** steps: behavior first, then the named
   metric. Run allocation assertions on optimized code
   (`DOTNET_TieredCompilation=0` or after tier-up).
1. Compare baseline and candidate BenchmarkDotNet exports with
   `scripts/compare_benchmarks.py` and re-run the application-level
   workload. Keep the change only if the target metric moved beyond the
   run-to-run noise and nothing else regressed.
1. Report using [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| `Split`/`Substring`/`Trim` allocations while parsing | [Span slicing](references/allocation.md#span-slicing-instead-of-substring-and-split) |
| Temporary `byte[]`/`char[]` per call | [stackalloc + pool](references/allocation.md#bounded-stackalloc-with-arraypool-fallback), [ArrayPool](references/allocation.md#arraypool-rent-and-return) |
| `new string(char[])`, `ToArray()` then string | [string.Create](references/allocation.md#stringcreate) |
| `string.Format`/boxing when writing to buffers | [TryWrite](references/allocation.md#trywrite-and-ispanformattable-into-caller-storage) |
| `+=` on strings in loops | [StringBuilder](references/allocation.md#presized-stringbuilder) |
| Closure/delegate allocations at call sites | [Static lambdas](references/allocation.md#static-lambdas-and-state-passing-overloads) |
| Boxing of struct keys in dictionaries/sets | [IEquatable keys](references/allocation.md#iequatable-on-struct-keys) |
| LINQ iterators in hot loops | [LINQ to loop](references/allocation.md#linq-pipeline-to-loop) |
| List/dictionary growth copies | [Presizing](references/allocation.md#presized-collections) |
| Double lookups on dictionary updates | [GetValueRefOrAddDefault](references/allocation.md#collectionsmarshalgetvaluereforadddefault) |
| `List<T>` enumerator overhead in hot loops | [AsSpan](references/allocation.md#collectionsmarshalasspan) |
| `Task<T>` allocations on synchronous hits | [ValueTask](references/allocation.md#valuetask-for-synchronous-completion) |
| `IndexOfAny(char[])` over a fixed set | [SearchValues](references/allocation.md#searchvalues) |
| Read-mostly lookup tables | [Frozen collections](references/allocation.md#frozen-collections) |
| Key strings created only to look up | [Alternate lookup](references/allocation.md#dictionary-alternate-lookup) |
| `params T[]` allocations | [params span](references/allocation.md#params-readonlyspan) |
| Virtual calls on leaf types | [sealed](references/codegen.md#sealed-classes) |
| `CORINFO_HELP_RNGCHKFAIL` in hot loops | [Bounds checks](references/codegen.md#bounds-check-elimination-by-slicing) |
| Scalar loops over large primitive arrays | [BCL vectorized APIs](references/codegen.md#vectorized-bcl-primitives), [Vector of T](references/codegen.md#portable-simd-with-vector-of-t) |
| Delegate or interface calls per element | [Struct generics](references/codegen.md#struct-generic-specialization) |
| Small helper not inlined in a hot loop | [AggressiveInlining](references/codegen.md#aggressiveinlining) |
| Zeroing cost of large stack buffers | [SkipLocalsInit](references/codegen.md#skiplocalsinit) |
| `new Regex` per call, regex startup | [GeneratedRegex](references/codegen.md#generatedregex) |
| Replacing `HasFlag` | [HasFlag semantics](references/codegen.md#enumhasflag-semantics) |
| `IEnumerable<T>` parameters in hot APIs | [Span parameters](references/codegen.md#span-parameters-instead-of-ienumerable) |
| Contended `lock (object)` | [Lock type](references/concurrency.md#systemthreadinglock), [Interlocked](references/concurrency.md#interlocked-instead-of-a-lock) |
| Interlocked per item in `Parallel.For` | [Thread-local aggregation](references/concurrency.md#parallelfor-with-thread-local-state) |
| Unbounded producer/consumer queues | [Bounded channel](references/concurrency.md#bounded-channel-of-t) |
| `.Result`/`.Wait()` on tasks, thread-pool starvation | [Async all the way](references/concurrency.md#async-all-the-way-instead-of-sync-over-async) |
| Continuations posted to a UI/sync context in libraries | [ConfigureAwait](references/concurrency.md#configureawaitfalse-in-library-code) |
| P/Invoke marshalling cost, AOT warnings | [LibraryImport](references/interop.md#libraryimport-source-generated-pinvoke) |
| Native strings built per call | [UTF-8 literals](references/interop.md#utf-8-string-literals-for-native-calls) |
| Callback delegates for native code | [Function pointers](references/interop.md#function-pointers-and-unmanagedcallersonly) |
| Native handle leaks or double frees | [SafeHandle](references/interop.md#safehandle-for-owned-native-resources) |
| Repeated pinning of long-lived buffers | [Pinned object heap](references/interop.md#pinned-object-heap-arrays) |
| Struct marshalling copies | [Blittable structs](references/interop.md#blittable-structs) |
| Startup JIT time | [ReadyToRun](references/runtime-config.md#readytorun), [NativeAOT](references/runtime-config.md#native-aot) |
| Steady-state throughput after warmup | [Tiered PGO](references/runtime-config.md#tiered-pgo) |
| GC pauses or heap size in servers/containers | [Server GC](references/runtime-config.md#server-gc), [DATAS](references/runtime-config.md#datas), [ConserveMemory](references/runtime-config.md#conserve-memory) |

## Rules

- Release build, no debugger, same machine, same inputs, same runtime for
  baseline and candidate. Follow BenchmarkDotNet's
  [good practices][good-practices], including consuming every result.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric does not move; do not keep "harmless"
  rewrites.
- A benchmark whose candidate does less work (skipped validation, different
  input, cached result) is invalid even if faster.
- Never widen a public API, change exception types, change culture or
  ordering behavior, or drop overflow checks to get speed. The cards list
  the semantic traps for each construct.
- Runtime settings (GC mode, tiering, ReadyToRun, NativeAOT) change the whole
  process. Apply them only with an application-level measurement and state
  the deployment consequence.
- `DisassemblyDiagnoser` does not run on macOS in BenchmarkDotNet 0.15.8; use
  `DOTNET_JitDisasm` there ([JIT disassembly][jitdisasm]).

## Bundled tools

- `assets/examples/verify.sh verify|runtime|benchmark|measure`: builds the
  construct catalog in a temp copy; `verify` runs every equivalence and
  allocation oracle, `measure` runs BenchmarkDotNet short jobs with JSON
  export. Requires the .NET 10 SDK.
- `scripts/compare_benchmarks.py`: compares two BenchmarkDotNet CSV exports
  by full row identity and exits 1 on a regression beyond a threshold; run
  with `--help` for columns and units.
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): BenchmarkDotNet anatomy, jobs,
  allocation assertions, `DOTNET_JitDisasm`, counters, traces, MSBuild
  properties, export comparison.
- [Allocation](references/allocation.md): spans, pooling, strings,
  closures, boxing, LINQ, presizing, collections, `ValueTask`, lookups.
- [Code generation](references/codegen.md): dispatch, bounds checks, SIMD,
  inlining, regex, flags.
- [Concurrency](references/concurrency.md): locks, atomics, parallel
  aggregation, channels, async boundaries.
- [Interop](references/interop.md): P/Invoke, callbacks, handles, pinning,
  native-library workloads (SDL3, BASS, fonts, images).
- [Runtime configuration](references/runtime-config.md): tiering, PGO,
  ReadyToRun, NativeAOT, GC modes.
- [Sources](references/sources.md): primary documentation per card.

## Completion evidence

The final report contains:

- target framework, language version, runtime, OS/CPU, and the evaluated
  build properties that affect code generation;
- the profile or counter output that attributed the cost;
- the construct applied, with the card's preconditions checked;
- the oracle command and its result, including edge cases;
- baseline and candidate numbers with units, error/StdDev, and allocation,
  from the same job and machine, plus the application-level result;
- anything not run (for example, Windows-only diagnosers, other runtimes)
  stated as not verified.

[good-practices]: https://benchmarkdotnet.org/articles/guides/good-practices.html

[jitdisasm]: references/measurement.md#jit-disassembly-with-dotnet_jitdisasm
