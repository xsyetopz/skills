# Measure C# and .NET performance, including .NET 10 and C# 14

## Establish the actual configuration

Read `global.json`, project and shared build properties, package versions,
target frameworks, and launch/publish settings. Use the selected SDK's evaluated
MSBuild properties and build output when conditions or imports matter; grepping
XML does not establish the effective configuration. Record JIT versus NativeAOT,
tiering/PGO, ReadyToRun, GC mode, architecture, and relevant environment
overrides. Do not infer a disabled optimization from an absent explicit
property; defaults and runtime configuration matter.

For a .NET 10 / C# 14 task, verify `net10.0` and the effective language version.
Do not upgrade another target merely to use a new construct. Avoid an unbounded
`LangVersion=latest` when reproducible compiler selection is required. Run
Release measurements without a debugger; keep startup and warmed steady-state
questions separate.

## Attribute and change

Use existing BenchmarkDotNet benchmarks for isolated managed operations and
runtime diagnostics for application behavior. Start with counters to identify
broad symptoms, then an appropriate CPU/allocation trace or heap investigation.
Allocated bytes per operation, live heap, GC count, and pause time are different
quantities; one does not establish the others.

Inspect repeated enumeration, LINQ materialization, boxing, closure capture,
iterator/state-machine allocation, string formatting, and buffer copies where
the trace attributes cost. Do not blanket-ban LINQ, interfaces, async,
delegates, or exceptions. The compiler/JIT may optimize a construct, and
removing it may change semantics or make a larger cost worse.

Choose spans for bounded synchronous views when they fit ownership. A span is
not owned storage. Keep an owner alive for `Memory<T>` or pooled memory crossing
asynchronous work. `ArrayPool<T>.Rent` may return a larger array: track logical
length, return to the correct pool once in `finally`, clear
sensitive/reference-bearing contents according to the contract, and prevent use
after return.

`CollectionsMarshal.AsSpan` exposes a list's storage; do not structurally mutate
the list while the span is borrowed. Large structs can increase copying and
register pressure. `in`, `ref`, and `ref readonly` can change aliasing and
produce defensive copies depending on use; inspect code generation rather than
declaring all by-reference access faster.

C# 14 span conversions can affect overload resolution. Extension members,
`field`-backed properties, and lambda syntax are not speedup guarantees. Verify
which overload and lowering the compiler selects. Preserve caller behavior when
replacing an enumerable API with a span-only API.

For flags of the same enum type, `Enum.HasFlag(mask)` has all-bits semantics:
`(value & mask) == mask`, including true for a zero mask. `(value & mask) != 0`
is not equivalent for zero or multibit masks. Preserve type checking and measure
before replacing an intrinsic-friendly call.

## Compare honestly

Keep all benchmark dimensions: type/method, parameters, runtime, job, build and
relevant environment. Do not overwrite rows keyed only by method name or compare
only the intersection of exported results. Inspect failed benchmarks and missing
rows. Prefer the benchmark framework's native output and analysis over a
home-grown Markdown/CSV parser that guesses units or number formats.

Use representative distributions, consume outputs, and keep setup placement
consistent. Investigate both latency and allocation regressions. If unsafe code,
callbacks, or a binding is involved, follow the separately linked interop
reference before changing ownership or representation.

Sources: [C# 14][c-14], [Enum.HasFlag][enum-hasflag],
[dotnet-counters][dotnet-counters], [BenchmarkDotNet good
practices][benchmarkdotnet-good-practices], [MSBuild command-line
reference][msbuild-command-line-reference].

## Executable fixtures

Requires .NET 10 SDK / C# 14 and POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in
[the csharp assets](../assets/examples). Copy that directory intact when
adapting a fixture. Run only this language; the target project keeps its own
toolchain.

### Semantic regression cases

Source: [Semantics.cs][ref-semantics-cs].

| Case | Required contract |
| --- | --- |
| 1 | Ordinal versus culture-sensitive matching |
| 2 | Enumerate a source once |
| 3 | Snapshot versus shared array |
| 4 | Single-consumption ValueTask contract |
| 5 | Return-to-pool lifetime using a deterministic test pool |
| 6 | All flag bits versus any flag bit |
| 7 | Cancellation propagation |
| 8 | Checked integer overflow |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The
[shared contract](dotnet-csharp-performance-executable-performance-fixtures.md)
explains input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Copy [the csharp asset directory](../assets/examples) intact. Run the following
commands in its `benchmarks/` subdirectory.

The `benchmarks/` project is the experiment entry point. The project pins
BenchmarkDotNet 0.15.8, a verified upstream release, but does not invent a
resolved lockfile. Provision .NET 10, review and run `dotnet restore`, retain
the resulting native lock for the experiment and use
`dotnet restore --locked-mode` thereafter.

```sh
dotnet run -c Release -- --filter '*DelimiterBench*' --exporters csv json
```

The complete native BenchmarkDotNet CLI is forwarded by `BenchmarkSwitcher`. Use
its declared jobs/runtimes for actual comparisons; do not flatten them into a
made-up metric format. The independent expected count is checked in setup; input
generation is outside measurement, and returned values are consumed by the
harness. Split and scan perform the same UTF-16 delimiter-count contract. Do not
infer equivalence for splitting on arbitrary strings or grapheme clusters.

Run warmed-service and cold-process questions separately.
`runtime-experiments.sh` operates on the neighboring comparison CLI and
explicitly tests startup-shaped PGO-on/off invocations; it is not a steady-state
PGO benchmark. Do not install a global `Directory.Build.props` that forces PGO,
AOT, server GC, unsafe code or ReadyToRun into unrelated projects.

For CSV comparisons across revisions, preserve every benchmark identity column;
use `scripts/compare_benchmarks.py` from the skill root only after environment
comparability and missing/error rows have been checked. Its threshold result is
not a significance test. Compilation requires the declared SDK and benchmark
dependencies.

Sources: [source][source] and [source][source-2]

## Failure reproduction

Source: [the isolated reproducer][ref-the-isolated-reproducer]. From the skill
root, run `sh assets/examples/verify.sh reproduction`. Direct commands below
assume a clean copy of the reproduction directory.

Expected: the optimization preserves ordinal case-insensitive equality.

Actual: Turkish culture comparison disagrees with ordinal comparison for `FILE`
and `file`. The verifier copies this project to a temporary directory and runs
it with .NET 10. Exit zero means the mismatch was reproduced.

[c-14]: https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-14
[enum-hasflag]:
  https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag?view=net-10.0
[dotnet-counters]:
  https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters
[benchmarkdotnet-good-practices]:
  https://benchmarkdotnet.org/articles/guides/good-practices.html
[msbuild-command-line-reference]:
  https://learn.microsoft.com/en-us/visualstudio/msbuild/msbuild-command-line-reference
[source]: https://benchmarkdotnet.org/articles/overview.html
[source-2]: https://github.com/dotnet/BenchmarkDotNet/releases/tag/v0.15.8
[ref-the-fixture-execution-contract]:
  dotnet-csharp-performance-executable-performance-fixtures.md
[ref-semantics-cs]: ../assets/examples/correctness/Semantics.cs
[ref-the-isolated-reproducer]: ../assets/examples/reproduction
