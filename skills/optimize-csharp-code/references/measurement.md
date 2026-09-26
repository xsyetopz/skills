# Measurement constructs

Tools to attribute a cost and prove a change moved it. Every other
card's **Verify** section uses them.

## Contents

- Effective MSBuild properties
- BenchmarkDotNet benchmark class
- BenchmarkDotNet jobs and exporters
- Comparing benchmark exports
- Allocation assertions with GetAllocatedBytesForCurrentThread
- JIT disassembly with DOTNET_JitDisasm
- DisassemblyDiagnoser
- dotnet-counters
- dotnet-trace

## Effective MSBuild properties

**Definition.** `dotnet msbuild <project> -getProperty:A,B,C` evaluates the
project (including `Directory.Build.props`, imports, and conditions) and
prints the resulting property values without building
([MSBuild CLI][msbuild-cli]).

**Use when.**

- Before any optimization: record what the build uses.

**Do not use when.**

- The question is what the *running process* uses: environment variables
  can override runtime settings. Use the runtime probe for that.

**Example.**

```sh
dotnet --info
dotnet msbuild src/App/App.csproj -p:Configuration=Release \
  -getProperty:TargetFramework,LangVersion,Optimize,TieredPGO \
  -getProperty:ServerGarbageCollection,PublishAot,PublishReadyToRun \
  -getProperty:InvariantGlobalization,AllowUnsafeBlocks
```

Multi-targeted projects need `-p:TargetFramework=net10.0` to evaluate one
framework.

**Cost removed.** Wrong conclusions from reading raw XML, where conditions
and imports change values. The output is a text dump to diff between
baseline and candidate.

**Verify.**

1. Save the output with the baseline results and diff it against the
   candidate's. Any difference other than the intended one invalidates the
   comparison.

## BenchmarkDotNet benchmark class

**Definition.** A public class with `[Benchmark]` methods, run through
`BenchmarkRunner`/`BenchmarkSwitcher`. BenchmarkDotNet builds a separate
Release process per job, runs warmup and measured iterations, and reports
mean, error, standard deviation, and (with `[MemoryDiagnoser]`) allocated
bytes per operation
([overview](https://benchmarkdotnet.org/articles/overview.html)).

**Use when.**

- Measuring an isolated method or a small call graph with controlled
  inputs.

**Do not use when.**

- The effect depends on the whole application (I/O, contention, GC over
  many requests): use the app's load test with counters.

**Example.**

```csharp
[MemoryDiagnoser]
public class AllocationBenchmarks
{
    private const string Csv = "12;7;-3;40;18;99;-100;5";

    [Benchmark(Baseline = true)]
    public int SplitParse() => SpanParsing.BaselineSum(Csv);

    [Benchmark]
    public int SpanParse() => SpanParsing.CandidateSum(Csv);
}
```

Rules: return the result (dead-code elimination otherwise removes the
work), put setup in `[GlobalSetup]`, use `[Params]` for input sizes, and
mark exactly one `Baseline = true` per class so the `Ratio` column is
meaningful
([good practices][good-practices]).

**Cost removed.** Noise and bias of ad-hoc `Stopwatch` loops (no warmup,
dead code elimination, debug builds).

**Verify.**

1. The run log shows `Release` and no debugger warning.
1. The summary table has `Error` and `StdDev`. A difference smaller than
   the combined error is not a result.

## BenchmarkDotNet jobs and exporters

**Definition.** A job sets launch, warmup, and iteration counts. `--job
dry` runs each benchmark once (harness smoke test, no timing value);
`--job short` uses 3 warmups and 3 iterations in 1 launch; the default job
chooses counts adaptively for precision. `--exporters json` writes
machine-readable results; `--filter` selects benchmarks by glob
([console arguments][console-arguments]).

**Use when.**

- `dry`: CI smoke checks that benchmarks still compile and run
  (`sh verify.sh benchmark`).
- `short`: quick local comparisons during iteration.
- default: numbers to report or gate on.

**Do not use when.**

- Reporting `dry` output as timing, or gating CI on `short` results with
  wide error bars.

**Example.**

```sh
dotnet run -c Release --project bench -- --filter '*Parse*' \
  --job short --exporters json --artifacts ./bench-results
```

Pass one `--filter` glob. Measured: listing several globs after one
`--filter` ran only the first class.

**Cost removed.** Wasted time on precise runs during exploration, and
imprecise numbers in reports.

**Verify.**

1. `./bench-results/results/*-report-full-compressed.json` exists per class.
1. The log line `// ***** Found N benchmark(s) in total *****` matches the
   expected number.

## Comparing benchmark exports

**Definition.** `scripts/compare_benchmarks.py` compares two CSV exports
(`--exporters csv`) row by row using explicit identity columns, converts
units, and exits `0` (within threshold), `1` (regression), or `2` (invalid
or incomparable input).

**Use when.**

- Gating a change on baseline versus candidate exports from the same
  machine and job.

**Do not use when.**

- The exports come from different jobs, runtimes, or machines: the
  script refuses rows whose identity columns differ, by design.

**Example.**

```sh
python3 scripts/compare_benchmarks.py --help
python3 scripts/compare_benchmarks.py \
  assets/benchmark-csv/baseline.csv assets/benchmark-csv/candidate.csv
```

**Cost removed.** Manual table reading and silently mismatched rows.

**Verify.**

1. `python3 scripts/test_compare_benchmarks.py` passes.
1. The calling script checks the exit code (`$?`), not only the output.

## Allocation assertions with GetAllocatedBytesForCurrentThread

**Definition.** `GC.GetAllocatedBytesForCurrentThread()` returns the total
bytes allocated by the calling thread. The difference around a call is
that call's allocation, excluding other threads
([API]).

**Use when.**

- A unit test must lock in "this path allocates 0 B" or "less than
  before", so regressions fail CI.

**Do not use when.**

- The code under test allocates on other threads (thread pool, timers):
  use `GC.GetTotalAllocatedBytes(precise: true)` in an isolated process or
  a BenchmarkDotNet `[MemoryDiagnoser]` run.
- The process runs tier-0 code: unoptimized code can allocate where
  optimized code does not (measured: 48 B versus 0 B for a `TryWrite`
  call). Run such tests with `DOTNET_TieredCompilation=0`.

**Example.**

```csharp
public static long AllocatedBytes(Action action)
{
    action(); // warm up: JIT, static constructors, pools
    long before = GC.GetAllocatedBytesForCurrentThread();
    action();
    return GC.GetAllocatedBytesForCurrentThread() - before;
}
```

Allocate test inputs outside the measured lambda. Measured: building a
4,000-character input string inside the lambda produced a false 16,240 B
failure.

**Cost removed.** Unnoticed allocation regressions.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints `ALLOC` lines and
   `VERIFY PASSED`.

## JIT disassembly with DOTNET_JitDisasm

**Definition.** `DOTNET_JitDisasm=<pattern>` (.NET 7+) makes the release
runtime print the native code for matching methods to stdout as they are
compiled. Patterns match `Type:Method`, a method name, or wildcards.
`DOTNET_JitStdOutFile=<path>` redirects the listing
([JIT disassembly][jit-disassembly]).

**Use when.**

- Confirming a codegen claim: a bounds check (`CORINFO_HELP_RNGCHKFAIL`),
  an allocation helper (`CORINFO_HELP_NEW*`), an indirect call (`blr` on
  Arm64, `call [rax+...]` on x64), or vector instructions.

**Do not use when.**

- The method is inlined into its caller: it gets no listing of its own.
  Inspect the caller, or add
  `[MethodImpl(MethodImplOptions.NoInlining)]` temporarily.

**Example.**

```sh
DOTNET_TieredCompilation=0 DOTNET_JitDisasm='BoundsChecks:*' \
  dotnet bin/Release/net10.0/Constructs.dll verify \
  | grep -E 'Assembly listing|RNGCHK'
```

With tiering on, the first listing is `Tier0` and a later one `Tier1`.
Read the `Tier1`/`FullOpts` listing.

**Cost removed.** Guessing about generated code.

**Verify.**

1. The listing header names the method and `(FullOpts)` or `(Tier1)`.

## DisassemblyDiagnoser

**Definition.** `[DisassemblyDiagnoser]` makes BenchmarkDotNet export the
benchmarked method's assembly next to the results
([diagnosers](https://benchmarkdotnet.org/articles/configs/diagnosers.html)).

**Use when.**

- Running on Windows or Linux and keeping disassembly with the benchmark
  results.

**Do not use when.**

- Running on macOS with BenchmarkDotNet 0.15.8: validation fails with
  "Only Windows and Linux are supported in DisassemblyDiagnoser without
  Mono" and no benchmark in the run executes. Use `DOTNET_JitDisasm`.

**Example.**

```csharp
[DisassemblyDiagnoser(maxDepth: 1)]
public class CodegenBenchmarks { /* ... */ }
```

**Cost removed.** A separate `DOTNET_JitDisasm` run to see the
benchmarked code: the listing is exported with the same run's results.

**Verify.**

1. `results/*-asm.md` exists after the run.

## dotnet-counters

**Definition.** `dotnet-counters monitor|collect --process-id <pid>
--counters System.Runtime` reads runtime metrics from a running process.
On .NET 9+ the `System.Runtime` meter publishes, among others,
`dotnet.gc.collections`, `dotnet.gc.heap.total_allocated`,
`dotnet.gc.last_collection.heap.size`, `dotnet.gc.pause.time`,
`dotnet.thread_pool.queue.length`, `dotnet.monitor.lock_contentions`, and
`dotnet.jit.compiled_methods`
([runtime metrics][runtime-metrics],
[dotnet-counters]).
Runtimes before .NET 9 publish the older EventCounter names instead
(`gc-heap-size`, `alloc-rate`, `time-in-gc`)
([available counters][available-counters]).

**Use when.**

- First look at a running app: decide whether the cost is
  GC/allocation, thread pool, contention, or CPU before choosing a trace.

**Do not use when.**

- The question is *which method* causes it: counters do not attribute.

**Example.**

```sh
dotnet tool install --global dotnet-counters
dotnet-counters monitor --process-id 1234 --counters System.Runtime
dotnet-counters collect --process-id 1234 --counters System.Runtime \
  --format json --output counters.json
```

**Cost removed.** Choosing a trace blind: counters name the cost class
(GC, thread pool, contention, JIT) from the running process, without a
restart.

**Verify.**

1. Collect under the same load before and after, and compare the named
   metric (for example `dotnet.gc.heap.total_allocated` per request,
   `dotnet.gc.pause.time`, `dotnet.monitor.lock_contentions`).

## dotnet-trace

**Definition.** `dotnet-trace collect` records an EventPipe trace
(`.nettrace`) from a process: CPU samples, GC events, allocation ticks,
contention, exceptions
([dotnet-trace]).

**Use when.**

- Counters show a cost class and the responsible call stacks are
  needed.

**Do not use when.**

- Tracing overhead would distort a latency measurement: keep traced and
  untraced runs separate.

**Example.**

```sh
dotnet tool install --global dotnet-trace
dotnet-trace collect --process-id 1234 --profile cpu-sampling \
  --output trace.nettrace
dotnet-trace convert trace.nettrace --format Speedscope
```

Open the `.speedscope.json` at speedscope.app, or the `.nettrace` in
PerfView or Visual Studio. Profile names differ between tool versions:
run `dotnet-trace list-profiles` for the installed version.

**Cost removed.** Editing the wrong method: the trace attributes the cost
class that counters found to call stacks.

**Verify.**

1. The hot frame named in the hypothesis appears in the baseline trace,
   and its inclusive share drops in the candidate trace under the same
   load.

[msbuild-cli]: https://learn.microsoft.com/en-us/visualstudio/msbuild/msbuild-command-line-reference
[good-practices]: https://benchmarkdotnet.org/articles/guides/good-practices.html
[console-arguments]: https://benchmarkdotnet.org/articles/guides/console-args.html
[api]: https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread
[jit-disassembly]: https://devblogs.microsoft.com/dotnet/performance_improvements_in_net_7/#jit
[runtime-metrics]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/built-in-metrics-runtime
[dotnet-counters]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters
[available-counters]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/available-counters
[dotnet-trace]: https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace
