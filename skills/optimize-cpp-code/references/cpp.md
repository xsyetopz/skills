# C++ performance

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
allocator traffic, and false sharing using the actual data distribution.
Separate C allocation/lifetime rules from C++ RAII and object construction;
`std::move` permits moving but does not guarantee no copy or no allocation.

Preserve defined behavior: bounds, alignment, object lifetime, integer overflow,
strict aliasing, and iterator/reference validity. A benchmark that invokes
undefined behavior is not evidence of a valid speedup. Use compiler optimization
remarks or disassembly to check an intended vectorization or dispatch change.
Keep a correct scalar path and runtime CPU dispatch when supporting machines
without the selected instruction set.

Benchmark outputs must remain observable so that dead-code elimination cannot
remove the work. Use the harness's anti-optimization mechanisms and realistic
inputs; volatile accesses are not a universal substitute for a proper harness.
Keep thread count, affinity, allocator, and NUMA placement comparable where they
matter.

For atomics, specify the synchronization relation and lifetime contract before
weakening memory ordering. Fewer locks do not prove less contention or
correctness. Test the affected error, cleanup, and concurrent paths separately
from timing.

Sources: [Clang optimization remarks][clang-optimization-remarks], [Google
Benchmark guide][google-benchmark-guide], [GCC instrumentation
options][gcc-instrumentation-options].

## Executable fixtures

Requires a C++17 compiler and POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in [the c-cpp
assets](../assets/examples). Copy that directory intact when adapting a fixture.
Run only this language; the target project keeps its own toolchain.

### Semantic regression cases

Source: [semantics.cpp][ref-semantics-cpp].

| Case | Required contract |
| --- | --- |
| 1 | Checked integer addition |
| 2 | Bit representation, not numeric conversion |
| 3 | Overlapping copy direction without undefined behavior |
| 4 | Stable logical identity after compaction |
| 5 | Borrowed view versus value snapshot |
| 6 | Adjacent erase traversal |
| 7 | Atomic read-modify-write, not separate atomic load/store |
| 8 | Signed-zero preservation |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The [shared contract](executable-fixtures.md) explains
input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Copy [the c-cpp asset directory](../assets/examples) intact. Run the following
commands in its `benchmarks/` subdirectory.

Provision a reviewed Google Benchmark installation and CMake toolchain; this
project uses `find_package`, not a hidden network download or vendored copy.
Build the copied native project:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
./build/delimiter_bench --benchmark_repetitions=10 \
  --benchmark_out=results.json --benchmark_out_format=json
```

Use the actual executable location on multi-config generators/Windows. All
native benchmark options remain available. The two algorithms compute the same
byte-delimiter count. The fixture deliberately includes a result check and an
optimization barrier in each timed iteration, so their overhead is shared but
not magically absent. Inspect optimized assembly: both implementations may be
compiled to the same code. This example does not claim one is faster.

Input generation is outside timing. Add production-shaped distributions rather
than optimizing only the illustrative repeated input. Run sanitized correctness
builds separately from representative optimized timing. Provision the native
benchmark dependency before running this project.

Source: [source][source]

## Failure reproduction

Source: [the isolated reproducer][ref-the-isolated-reproducer]. From the skill
root, run `sh assets/examples/verify.sh reproduction`. Direct commands below
assume a clean copy of the reproduction directory.

Expected: a saved element handle remains valid after appending.

Actual: growth changes the allocation, so the saved pointer is invalidated. The
verifier copies `repro.cpp` to a temporary directory, compiles it as C++17, and
runs it. Exit zero means the invalidation was reproduced.

[clang-optimization-remarks]: https://clang.llvm.org/docs/UsersManual.html#options-to-emit-optimization-reports
[google-benchmark-guide]: https://google.github.io/benchmark/user_guide.html
[gcc-instrumentation-options]: https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
[source]: https://google.github.io/benchmark/user_guide.html

[ref-the-fixture-execution-contract]: executable-fixtures.md
[ref-semantics-cpp]: ../assets/examples/correctness/semantics.cpp
[ref-the-isolated-reproducer]: ../assets/examples/reproduction
