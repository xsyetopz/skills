# Profiling and benchmark protocol for C Native Performance

## Choose the evidence layer

Use a production/representative trace to identify the component, a component
profile to identify the cost center, and a microbenchmark only to compare a
well-isolated operation. Preserve the chain from system objective to benchmark.

Target tools: the project profiler; commonly Linux perf, Instruments, ETW/WPA,
Valgrind/Callgrind, compiler optimization reports, sanitizers, and the project
benchmark harness. Select only tools that answer a defined question and are
supported in the target environment. Sampling profiles estimate where time is
spent; instrumentation can alter timing; allocation traces differ from live
retention; generated code/disassembly explains compiler behavior but not
workload importance.

## Benchmark contract

Use a repository-native C benchmark harness or a small process/function
benchmark with independent result checks; do not require C++ Google Benchmark
for a C-only task. Before timing, assert independent expected results and run
representative boundary/error cases. Keep fixture generation outside measurement
unless generation is part of the operation. Avoid shared mutable state across
iterations unless it models the workload and is reset deterministically.

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
