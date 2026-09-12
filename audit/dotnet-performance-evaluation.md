# .NET performance evaluation

Evaluated on 2026-09-12. Added one explicit-only `optimize-dotnet-code` skill,
absorbing useful material from three version-specific source archives without
forcing a runtime upgrade or copying their unsafe optimization defaults.

## Real runtime and tooling

Validation used .NET SDK 10.0.400, MSBuild 18.9.6, runtime 10.0.11, macOS arm64,
BenchmarkDotNet 0.15.8, and diagnostic tools 10.0.745401. Versions were obtained
from the installed toolchain and NuGet package index, not inferred from language
feature names. Isolated tool installation reported that package signature
verification was skipped; this is retained as an environment limitation, not
claimed provenance verification or a repository policy change.

The documented MSBuild query returned `net10.0`, C# `14.0`, optimization
enabled, and unchecked integer arithmetic for the default Release fixture. It is
an evaluated-property probe, not a recommendation to disable project overflow
checks.

Both documented launch-and-collect commands ran against an isolated five-second
order-total workload. Counter JSON contains 131 runtime metric events, including
allocation, GC and process metrics. The trace report includes the actual
`Totals.Materialized` method, array allocation and decimal addition, not merely
process startup. No user's existing application was attached to or modified.

Installed `list-profiles` showed a stale assumption in the initial draft:
`cpu-sampling` is now for Linux `collect-linux`, while portable `collect` uses
`dotnet-sampled-thread-time`. Corrected the command and distinguished wall-clock
stack occupancy from CPU utilization. The actual corrected capture exited zero.
No Linux kernel tracing, native profiler or GUI trace-viewer result is claimed.

## Observable behavior and measurements

The workload totals settled orders, including negative refund amounts. The
candidate removes intermediate `ToArray()` materialization while retaining
standard LINQ filtering and decimal summation. It introduces no custom parser,
unsafe access, pool, GC configuration or framework upgrade.

Correctness execution passed:

- 300 deterministic differential cases, including empty input and mixed positive
  and negative amounts;
- overflow preservation for both implementations;
- 64 enum value/mask combinations for the all-bits rewrite;
- counterexamples rejecting the archive's nonzero-AND rewrite for a composite
  mask and a zero mask.

These checks validate actual rewrite risks, not arbitrary syntax rules. The
fixture uses an unmodified array during each operation; it makes no promise of
equivalence when another thread mutates records during enumeration.

BenchmarkDotNet ran four benchmarks in separate generated processes, Release,
with memory diagnostics, three warmup iterations and three measured iterations.
For 128 orders, means were 641.7 ns and 591.8 ns; managed allocation was 2,128
and 64 bytes per operation. For 10,000 orders, means were 52.944 and 44.646
microseconds; allocation was 160,122 and 64 bytes. The larger case's standard
deviations were 0.267 and 0.360 microseconds. This short local run supports the
allocation improvement; its wide confidence intervals do not establish a durable
timing regression threshold, application-wide speedup, native-memory reduction
or p99.

The first benchmark attempt used the repository as its current directory.
BenchmarkDotNet failed generated-project discovery but exited zero with zero
executed benchmarks and an `NA` result. That attempt was rejected. Running from
the benchmark project directory completed all four expected cases. The guidance
now includes the working-directory boundary and requires actual result evidence,
not only a process exit code.

Actual execution of the archived comparison script returned zero for a missing
candidate mean and separately merged different runtime jobs. It was declined,
not promoted into a gate after superficial parser tests.

## Invocation and limits

Coordinator boundary review, not an independent agent or client-loader test:

- `Use $optimize-dotnet-code to reduce this endpoint's allocations`: selects the
  .NET measurement workflow, then needs the workload and runtime context.
- `Use $optimize-dotnet-code to review this native callback lifetime`: selects
  conditional memory/interop guidance; invocation does not prove native ABI
  facts.
- `This C# method is slow`: does not implicitly activate the manual skill.
- `Upgrade this service to .NET 10`: ordinary migration, not this skill's
  workflow.
- `Optimize this Rust parser`: does not select .NET guidance.
- `Plan a .NET module split`: architecture planning, not a performance workflow.

No .NET 8/9 runtime execution, Native AOT publication, native callback fixture,
unsafe soundness proof, managed-heap dump or production service load test is
claimed. Those require their own affected-path evidence when applicable.

Evidence is retained under `/tmp/dotnet-performance-evidence/`: the `Probe` and
`Bench` projects, correctness log, evaluated properties, runtime counter JSON,
trace and report, original and corrected benchmark logs, raw benchmark reports,
and source-comparator counterexample logs. No build artifacts enter the skill
package. Structural validation supplements rather than replaces this evidence.
