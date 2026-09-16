# C performance

Establish compiler/version, language standard, optimization and debug-info
flags, architecture, link-time optimization, profile-guided optimization, and
allocator. Compare deployment-compatible builds. `-march=native` can invalidate
portability; sanitizer and debug builds answer correctness questions but are not
interchangeable with production performance builds.

Use the project's benchmark first and platform-native profiling for the target
environment. Linux `perf` can attribute sampled CPU and hardware events when
permissions and hardware allow it. Check symbolization, inlining, and sample
coverage before assigning cost from a flame graph. A low cache-miss percentage
does not prove that memory latency is irrelevant.

Optimize the algorithm and memory access pattern before editing individual
instructions. Investigate working-set size, indirection, layout, copying,
allocator traffic, and false sharing using the actual data distribution. Track
every allocated object's owner, size, lifetime, and cleanup. A borrowed pointer
does not become owned merely because it is stored in a structure.

Preserve defined behavior: bounds, alignment, object lifetime, integer overflow,
strict aliasing, and validity of pointers into resized or compacted storage. A
benchmark that invokes undefined behavior is not evidence of a valid speedup.
Use compiler optimization remarks or disassembly to check an intended
vectorization or dispatch change. Keep a correct scalar path and runtime CPU
dispatch when supporting machines without the selected instruction set.

Benchmark outputs must remain observable so that dead-code elimination cannot
remove the work. Use the harness's anti-optimization mechanisms and realistic
inputs; volatile accesses are not a universal substitute for a proper harness.
Keep thread count, affinity, allocator, and NUMA placement comparable where they
matter.

For atomics, specify the synchronization relation and lifetime contract before
weakening memory ordering. Fewer locks do not prove less contention or
correctness. Test the affected error, cleanup, and concurrent paths separately
from timing.

Sources: [Clang optimization remarks][clang-optimization-remarks], [GCC
instrumentation options][gcc-instrumentation-options].

## Executable fixtures

The self-contained examples require C17 and POSIX `sh`; no C++ compiler is
needed. Read [the fixture contract](executable-fixtures.md) before running:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

Copy [the native examples](../assets/examples) intact before adaptation. The
[comparison functions](../assets/examples/comparisons/c_pairs.c) cover string
joining, byte histograms, matrix traversal, and filtering with independent
expected results. The preserved
[justfile](../assets/examples/comparisons/justfile) and [xmake
configuration](../assets/examples/comparisons/xmake.lua) supply optional native
build/sanitizer commands; the shell runner needs neither tool.

### Semantic regression cases

The [same-check pairs](../assets/examples/correctness/semantics.c) deliberately
use defined C behavior even on the faulty path. They are not timing baselines.

| Case | Required contract |
| --- | --- |
| 1 | Reject an addition outside the unsigned destination range |
| 2 | Preserve object bytes rather than convert numeric values |
| 3 | Copy overlapping ranges in the correct direction |
| 4 | Preserve logical identity after compaction |
| 5 | Preserve an owned snapshot after caller mutation |
| 6 | Remove adjacent matching elements without skipping |
| 7 | Retain embedded NUL bytes in length-delimited input |
| 8 | Preserve signed zero |

## Benchmark integration

Use the target's existing C benchmark runner. Adapt these callable operations,
keeping the required result observable and setup in the correct measurement
scope. The comparison CLI includes setup and printing; timing its process does
not establish steady-state function latency. Preserve native runner options,
compiler flags, allocator, and output format; do not add a custom measurement
schema. Correctness and sanitizer checks remain distinct from representative
optimized timing.

## Failure reproduction

[The binary-length reproducer](../assets/examples/reproduction/repro.c)
demonstrates that `strlen` truncates a length-delimited payload containing NUL.
The fixture requires three payload bytes; the erroneous text length is one. Exit
zero from this reproducer means that exact defect was observed, not that a fix
passed.

```sh
sh assets/examples/verify.sh reproduction
```

[clang-optimization-remarks]: https://clang.llvm.org/docs/UsersManual.html#options-to-emit-optimization-reports
[gcc-instrumentation-options]: https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
