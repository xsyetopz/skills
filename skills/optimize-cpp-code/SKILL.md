---
name: optimize-cpp-code
description: >-
  Optimizes measured C++ hot paths: allocations, copies and moves,
  string_view, containers, devirtualization, atomics, false sharing, checked
  with counters and assembly. Use when a C++ benchmark or profile shows the
  cost. Not for C-only code.
---

# Optimize C++ Code

Make a measured C++ hot path cheaper without changing observable
behavior. Each change applies one reference card to a cost that a
profile or counter attributes, is checked by an equivalence oracle, and
is kept only if the metric the card names improves: allocation calls,
copies or moves, hash or comparison counts, flushes, an instruction
pattern in the assembly, or a timing pair. The cards record where a
common construct measured as no difference or a slowdown, so read the
card before applying a construct.

## Workflow

1. Record the target: `c++ --version`, the libc++ version
   (`_LIBCPP_VERSION`, see
   [toolchain record](references/measurement.md#toolchain-and-sdk-record)),
   `-std=`, `-O` level, `-march`/`-mcpu`, LTO, hardening mode,
   exceptions and RTTI flags, and the deployment target. Keep them
   unless the task is the build configuration itself.
1. Reproduce the workload in an optimized build (`-O2` or the
   project's release flags). Pick the metric the user cares about:
   time per operation, end-to-end time, allocations, peak memory.
1. Attribute the cost before editing: a profile
   ([xctrace][xctrace] on macOS, `perf` on Linux), the
   [counting operator new][count-new], or the
   [copy/move counter][count-moves].
1. Choose one construct from the routing table whose **Use when**
   matches the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty input, one element, boundary values (`LONG_MIN`,
   `-0.0`), embedded NUL, non-ASCII bytes, missing keys, and error
   paths. `constructs verify` in the bundled catalog shows the shape.
1. Apply the change. Put a `// PERF:` comment on every lifetime
   assumption the change adds (a `string_view`, `span`, view, or
   reference into a container or buffer, a `pmr` arena, a relaxed
   atomic) stating why it holds, and run the sanitizers over it
   (`verify.sh sanitize` shows the command); state it if ASan was not
   run.
1. Verify with the card's **Verify** steps: behavior first, then the
   named metric. Assembly claims use `-S` on `extern "C"` `noinline`
   functions with the same flags as the timed build.
1. Measure baseline and candidate with the same compiler, SDK, flags,
   input, and machine (Google Benchmark if the project has it, else the
   [chrono harness][chrono] or [hyperfine][hyperfine]).
   Keep the change only if the difference repeats and the application
   workload also improves.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| `std::move(f())`, `return std::move(local)`, `-Wpessimizing-move` | [elision](references/objects.md#guaranteed-copy-elision-of-prvalues), [NRVO](references/objects.md#return-a-local-by-name-nrvo), [implicit move](references/objects.md#implicit-move-on-return) |
| Copies where moves were expected | [const local](references/objects.md#non-const-locals-for-values-that-will-be-moved), [last use](references/objects.md#stdmove-at-the-last-use), [noexcept move](references/objects.md#noexcept-move-constructor-for-vector-growth) |
| Containers or strings passed by value | [const&](references/objects.md#const-reference-for-read-only-parameters), [sink by value](references/objects.md#pass-by-value-and-move-for-sink-parameters), [span](references/containers.md#span-for-read-only-sequence-parameters) |
| `push_back(T{...})` | [emplace_back](references/objects.md#emplace_back-instead-of-push_back-of-a-temporary) |
| `shared_ptr` copies, `ldadd`/`ldaddal` in hot code | [make_shared](references/objects.md#make_shared-instead-of-shared_ptr-from-new), [unique_ptr](references/objects.md#unique_ptr-instead-of-shared_ptr), [by const&](references/objects.md#pass-shared_ptr-by-const-reference) |
| Vector growth reallocations; memory kept after shrinking | [reserve](references/containers.md#vectorreserve), [shrink_to_fit](references/containers.md#shrink_to_fit), [clear reuse](references/containers.md#clear-to-reuse-a-buffer) |
| `substr`, `std::string const&` from literals | [SSO](references/containers.md#short-string-optimization-capacity), [view substrings](references/containers.md#string_view-for-substrings), [view params](references/containers.md#string_view-for-read-only-text-parameters) |
| Hash map rehashing, double lookups, `std::string(key)` probes | [reserve](references/containers.md#unordered_mapreserve), [try_emplace](references/containers.md#try_emplace-for-a-single-lookup), [heterogeneous](references/containers.md#heterogeneous-lookup-with-a-transparent-hash) |
| `std::map::find` hot, read-mostly tables | [hash map](references/containers.md#hash-map-instead-of-an-ordered-map-for-point-lookups), [sorted vector](references/containers.md#sorted-vector-with-lower_bound), [flat_map](references/containers.md#stdflat_map) |
| Many short-lived allocations per request | [pmr arena](references/containers.md#pmrmonotonic_buffer_resource) |
| `erase(it)` in a loop | [erase_if](references/containers.md#stderase_if-instead-of-erase-in-a-loop) |
| `blr` or vtable loads in a hot loop | [templates](references/codegen.md#templates-instead-of-virtual-dispatch), [CRTP](references/codegen.md#crtp-for-static-polymorphism), [visit](references/codegen.md#stdvariant-with-stdvisit), [get_if](references/codegen.md#stdvariant-with-get_if), [final](references/codegen.md#final-for-devirtualization) |
| `std::function` parameter called per element | [template callable](references/codegen.md#template-callable-instead-of-stdfunction) |
| Runtime-built constant tables, `__cxa_guard` | [constexpr table](references/codegen.md#constexpr-lookup-table), [consteval](references/codegen.md#consteval-for-guaranteed-compile-time-values) |
| Branch hints proposed | [likely/unlikely](references/codegen.md#likely-and-unlikely-attributes) (card measured a slowdown) |
| `__cxa_throw` or unwinding in the profile | [expected](references/codegen.md#stdexpected-for-frequent-failures), [exceptions](references/codegen.md#exceptions-for-rare-failures) |
| `brk` traps in indexing loops; hardening debate | [hardening mode](references/codegen.md#libc-hardening-mode) |
| Sorting cost, top-k, pipeline temporaries | [sort](references/codegen.md#stdsort-instead-of-stdstable_sort), [partial_sort](references/codegen.md#partial_sort-for-top-k), [ranges](references/codegen.md#lazy-ranges-views-instead-of-intermediate-containers) |
| Slow line output, `std::endl`, `std::print` | [newline](references/io.md#newline-instead-of-stdendl), [sync_with_stdio](references/io.md#sync_with_stdiofalse-and-cintienullptr), [buffer](references/io.md#build-text-in-a-buffer-and-write-once), [print](references/io.md#stdprint), [format_to](references/io.md#stdformat_to-into-a-reused-buffer) |
| `ostringstream`, `to_string`, `stol`, `istringstream` in loops | [to_chars](references/io.md#stdto_chars-for-numbers-to-text), [from_chars](references/io.md#stdfrom_chars-for-text-to-numbers) |
| seq_cst atomics, contended counters, adjacent per-thread slots | [relaxed](references/concurrency.md#memory_order_relaxed-for-event-counters), [acquire/release](references/concurrency.md#acquire-and-release-instead-of-seq_cst-for-publication), [padding](references/concurrency.md#padding-per-thread-data-against-false-sharing), [interference size](references/concurrency.md#hardware_destructive_interference_size), [local sums](references/concurrency.md#per-thread-accumulation-instead-of-a-shared-atomic) |
| Idle cores during a large sort or transform | [std::execution::par](references/concurrency.md#parallel-algorithms-with-stdexecutionpar) |
| Compiler flags, LTO, PGO, `restrict`, SoA, C allocators | the optimize-c-code skill |

## Rules

- Measure optimized builds only, with the same compiler, SDK, flags,
  and hardening mode for baseline and candidate. On macOS the libc++
  headers come from the SDK; a different `SDKROOT` is a different
  standard library.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric does not move: several cards record
  constructs that changed the assembly but not the time (`constexpr`
  table, `std::visit`) or made it slower (`[[unlikely]]`).
- A candidate that does less work is invalid: a skipped error check
  (`from_chars` without checking `ptr`), a dropped flush the user
  needs, a cached result, a smaller input, or an exception turned into
  a default value.
- Preserve semantics a rewrite can silently change: tie order
  (`stable_sort` vs `sort`, `partial_sort` ties), moved-from state
  being read, iterator and pointer invalidation after growth or
  `erase`, map iteration order, view and span lifetimes, whitespace and
  `+` handling in parsers, float formatting (`-0`, shortest form), and
  `std::reduce` grouping (its card shows it wrapping 32-bit sums).
- Allocation and copy assertions compare baseline and candidate
  counts measured in the same run; never assert an exact baseline
  count. Counts under ASan are not valid (it interposes `operator new`).
- Availability is per library and deployment target: check the
  feature-test macro (`__cpp_lib_flat_map`, `__cpp_lib_print`) and
  compile with the real `-mmacosx-version-min`. Parallel algorithms
  need `-fexperimental-library` on libc++; say so.
- Report only numbers you measured (with machine, compiler, and
  library) or numbers from a linked primary source.

## Bundled tools

`assets/examples/verify.sh` builds in a temporary directory, prints the
compiler, `SDKROOT`, and `_LIBCPP_VERSION`, and falls back to the
newest Command Line Tools SDK that links when the default SDK cannot:

- `verify` (default): equality oracles plus `ALLOC`, `COPIES`,
  `MOVES`, `HASHES`, `COMPARES`, `PREDICATE`, and `FLUSHES` assertions;
  identical stdout bytes from every printer.
- `benchmark`: runs every pair once; smoke only, no timing.
- `asm`: asserts `blr`, atomics, `__cxa_guard`, and `ldaddal`/`ldadd`
  per function on aarch64.
- `diagnose`: move warnings, the `consteval` compile error, and
  `-Wdangling-gsl`.
- `time [filter]`: chrono median timing of every pair.
- `io`: hyperfine over the stdout printers.
- `sanitize`: ASan and UBSan build of the oracles and a dangling
  `string_view` that must be reported.
- `hardening`: libc++ `NONE` versus `FAST` (`brk`, trap, hyperfine).
- `parallel`: `std::execution::par` versus sequential with oracles.

## References

- [Measurement](references/measurement.md): toolchain record, sink,
  chrono harness, counting `operator new`, copy/move counter, call
  counters, `-S`, diagnostics, sanitizers, hyperfine, Google Benchmark,
  xctrace.
- [Objects](references/objects.md): elision, moves, parameters, and
  smart pointers.
- [Containers](references/containers.md): vectors, strings, views,
  hash maps, flat maps, and `pmr`.
- [Code generation](references/codegen.md): dispatch, type erasure,
  compile-time evaluation, hints, errors, hardening, and algorithms.
- [I/O](references/io.md): streams, formatting, and `charconv`.
- [Concurrency](references/concurrency.md): memory order, false
  sharing, and parallel algorithms.

## Completion evidence

The final report contains:

- compiler version, `_LIBCPP_VERSION` (or the library in use),
  `SDKROOT` or sysroot, flags, OS, and CPU;
- the profile or counter output that attributed the cost;
- the card applied and each **Use when** / **Do not use when** item
  checked;
- the oracle command and result, including edge and error cases;
- the card's metric before and after (counts, assembly pattern, or
  timing with spread) from the same build and machine, and the
  application-level result;
- every check not run (sanitizers, other standard libraries, other
  architectures, Google Benchmark) stated as not verified.

[xctrace]: references/measurement.md#xctrace-time-profiler
[count-new]: references/measurement.md#counting-global-operator-new
[count-moves]: references/measurement.md#copy-and-move-counting-type
[chrono]: references/measurement.md#stdchrono-median-harness
[hyperfine]: references/measurement.md#hyperfine-for-whole-process-comparisons
