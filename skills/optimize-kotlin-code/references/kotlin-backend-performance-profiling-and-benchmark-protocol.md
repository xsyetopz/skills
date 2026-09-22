# Profiling and benchmark protocol for Kotlin Backend Performance

## Choose the evidence layer

Use a production/representative trace to identify the component, a component
profile to identify the cost center, and a microbenchmark only to compare a
well-isolated operation. Preserve the chain from system objective to benchmark.

Target tools: backend-specific profiler and benchmark harness; for Kotlin/JVM
commonly JFR/JMC/async-profiler/JMH, allocation/GC tools, coroutine diagnostics,
compiler reports, and project tests. Select only tools that answer a defined
question and are supported in the target environment. Sampling profiles estimate
where time is spent; instrumentation can alter timing; allocation traces differ
from live retention; generated code/disassembly explains compiler behavior but
not workload importance.

## Benchmark contract

Use a backend-matched benchmark; for JVM use JMH with target JDK/Kotlin/compiler
settings, forks/warmup/state and independent correctness; do not transfer JVM
results to Kotlin/Native or JS. Before timing, assert independent expected
results and run representative boundary/error cases. Keep fixture generation
outside measurement unless generation is part of the operation. Avoid shared
mutable state across iterations unless it models the workload and is reset
deterministically.

Separate cold start, warm steady state, throughput under load, and tail latency.
Report sample count, statistic, dispersion/confidence output provided by the
harness, and raw artifacts. Investigate bimodality, GC/JIT transitions, thermal
throttling, contention, background work, and environment drift instead of
selecting favorable runs.

## Comparison gate

A comparison is invalid when method/parameters/job/toolchain/runtime/build
configuration/hardware/input differ materially, rows are missing, units are
ambiguous, results are NaN/zero for impossible work, or the candidate performs
less work. Reject invalid data explicitly.
