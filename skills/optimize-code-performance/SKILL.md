---
name: optimize-code-performance
description: >-
  Profiles and speeds up C, C++, C#, Go, Java, JavaScript, Kotlin, Python,
  Rust, Scala, and Swift code for CPU time, latency, memory, and
  allocations. Use when a benchmark or profile shows a hot path. Not for
  TypeScript build speed.
---

# Optimize Code Performance

Make a measured hot path cheaper without changing observable behavior. A
change is kept only when a profile pointed at the cost, a test proves the
result is unchanged, and the metric improved on re-measurement.

## Rules

- Attribute the cost before editing. Run the profiler from the table below
  on a local reproduction or replay of the real workload, and name the
  function, allocation site, or wait that dominates. Profiling a production
  process needs the user's approval (overhead, customer data in samples).
  Optimizing code the profile does not show moves no metric and adds risk.
- Write the equivalence test first. Keep the old implementation as a
  baseline function and compare old and new on empty, boundary, error,
  aliasing, and ordering inputs. Faster code that changes results, error
  text, ordering, or nil versus empty is a regression.
- Benchmark release builds only: `-O2`, `cargo build --release`, Go default,
  `dotnet build -c Release`, `swift build -c release`, a JIT that has warmed up.
  Debug and unoptimized numbers point at different hot spots.
- Make the benchmark consume its result. Dead-code elimination deletes a
  loop whose output is unused, and constant inputs let the compiler fold
  the work. Use the harness sink (`Blackhole`, `black_box`, `b.Loop`,
  `DoNotOptimize`, `BenchmarkDotNet` return values) and inputs the
  compiler cannot see through.
- Warm up before timing on JIT runtimes (JVM, .NET, V8, PyPy) and
  discard the warmup. Cold-start cost is a separate metric: measure it
  only when startup is the complaint.
- Repeat and compare distributions, not single numbers. Run at least 10
  samples each for baseline and candidate on the same machine, inputs,
  and power state, and use the comparison tool of the harness (`benchstat`,
  `pyperf compare_to`, `criterion`, JMH error bars). A difference inside
  the noise is no difference: revert it. Do not rerun until a result
  becomes significant.
- Change one thing per measurement so the result is attributable. Revert
  a change whose metric shows no movement; a plausible rewrite often
  measures as nothing.
- Invalid speedups: less work (skipped validation, cached result, smaller
  input), a benchmark that measures setup, and a microbenchmark win that
  vanishes in the application. Re-run the application-level workload
  after the last change and report both numbers.
- Check the target, not the laptop. Record compiler and runtime versions,
  flags, CPU, and runtime settings (`GOMAXPROCS`, heap size, GC mode).
  Timings do not transfer between machines; allocation counts usually do.
- Build-wide switches (LTO, PGO, `-march=native`, GC settings) change the
  whole binary. `-march=native` produces binaries that crash on older
  CPUs in the fleet. Measure at application level, state the deployment
  consequence, and stop for the user's approval before changing the shipped
  build configuration.
- Keep public API and thread-safety contracts. Pooling, buffer reuse, and
  caching introduce aliasing and shared-state bugs; say what the caller
  may now not do.

## Workflow

1. Reproduce the workload and pick the metric: CPU time, tail latency,
   throughput, allocations per operation, live heap, or RSS.
1. Profile with the tool for the language and read its reference for the
   traps of that stack.
1. Write the baseline and the oracle test.
1. Apply one change, run the oracle, then the benchmark (at least 10
   samples each), then the comparison tool.
1. Keep or revert. Repeat from the new profile, since the top of a
   profile changes after each fix.
1. Report the profile that justified the change, the oracle result,
   before and after with their spread, and anything not measured.

## Languages

| Language | Profile and benchmark | Reference |
| --- | --- | --- |
| C | `perf record` (Linux) or WPA with ETW (Windows), `valgrind --tool=callgrind` (Linux), sanitizers, `-fopt-info` or `-Rpass` | [c](references/c.md) |
| C++ | `perf` and `heaptrack` (Linux) or WPA with ETW (Windows), Google Benchmark, `objdump -d -C` (`dumpbin /disasm` for MSVC) | [cpp](references/cpp.md) |
| C# | BenchmarkDotNet, `dotnet-counters`, `dotnet-trace` | [csharp](references/csharp.md) |
| Go | `go test -bench -benchmem -count 10`, `benchstat`, `pprof` | [go](references/go.md) |
| Java | JMH, JFR, `-Xlog:gc`, `-XX:+PrintCompilation` | [java](references/java.md) |
| JavaScript | `node --cpu-prof`, `--trace-deopt`, DevTools, `mitata` | [javascript](references/javascript.md) |
| Kotlin | JMH with `kotlinx-benchmark`, JFR, `javap -c` | [kotlin](references/kotlin.md) |
| Python | `pyperf`, `cProfile`, `tracemalloc`, `-X importtime` | [python](references/python.md) |
| Rust | Criterion or `divan`, `samply`, `cargo asm`, DHAT | [rust](references/rust.md) |
| Scala | JMH via `sbt-jmh`, JFR, `javap -c` | [scala](references/scala.md) |
| Swift | `package-benchmark`, Instruments, `-emit-sil` | [swift](references/swift.md) |

## Scripts

- `python3 scripts/compare_benchmarks.py BASELINE.csv CANDIDATE.csv --keys
  COL... --max-regression-percent N` compares two complete BenchmarkDotNet-style
  CSV tables row by row and fails on a duration regression. Every column
  must be a key, the metric, or ignored, so it never guesses row identity.
  Exit 0 within the threshold, 1 regression, 2 invalid input. Run it with
  `--help`. On Windows, use `py -3` for `python3`. For other harnesses use
  their own comparison tool.

## References

Read the language reference from the table before applying a change. Each
lists mistakes that look like optimizations and their fixes. Read
[jvm](references/jvm.md) as well when the code runs on the JVM and the
cost is JIT warmup, GC, or the JMH harness.
