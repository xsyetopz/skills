---
name: optimize-c-code
description: >-
  Profiles and optimizes C CPU time, memory, and I/O with sanitizers, compiler
  remarks, assembly, LTO, and PGO. Use when a C benchmark or profile shows the
  cost. Not for C++ code or style fixes.
---

# Optimize C Code

Make a measured C hot path cheaper without changing observable behavior.
Each change applies one reference card to a cost that a profile attributes,
is checked by an equivalence oracle under sanitizers, and is kept only if
the metric the card names improves: allocator calls, OS write calls, an
instruction pattern in `-S` output, an optimization record, or a timing
interval. The cards record where clang already does the rewrite (copy and
zero loops, read-only `strlen`), so read the card before applying a
construct; a hand-written change there is noise.

## Workflow

1. Record the target: `cc --version`, the standard (`-std=`), the
   optimization, target, LTO, and sanitizer flags from the build files,
   the linker, the libc, and the OS and CPU. Keep them unless the task is
   the build configuration itself.
1. Reproduce the workload with the release flags, never `-O0`. Pick the
   metric the user cares about: time per operation, wall time,
   allocator calls, peak memory, OS calls, or binary size.
1. Attribute the cost before editing:
   - CPU on macOS: `sample PID` or `xctrace record --template 'Time
     Profiler'` ([sample](references/measurement.md#sample),
     [xctrace](references/measurement.md#xctrace-time-profiler)); on
     Linux, [perf](references/measurement.md#linux-perf).
   - Allocator calls: [counting wrappers][count]; leaks only:
     [leaks](references/measurement.md#leaks-at-exit).
   - Codegen: [`-S`](references/measurement.md#assembly-inspection) and
     [remarks](references/measurement.md#optimization-remarks).
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty, one element, boundary lengths, overlapping ranges,
   `INT_MAX`/`INT_MIN`, embedded `'\0'`, and error paths.
1. Apply the change. Document every `restrict`, alignment, ownership,
   and buffer-size precondition in a comment at the definition.
1. Run the oracle under
   [ASan and UBSan](references/measurement.md#sanitizer-oracle-build),
   then check the card's metric.
1. Measure baseline and candidate with the same compiler, flags, input,
   and machine: the [monotonic timing
   loop](references/measurement.md#monotonic-clock-timing-loop) for a
   function, [hyperfine](references/measurement.md#hyperfine-for-whole-programs)
   for a program. Repeat; keep the change only when the difference
   exceeds the run-to-run spread and the application workload improves.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| Value reloaded after a store; overlap checks; copy loop not `memcpy` | [restrict](references/codegen.md#restrict-pointers) |
| `strlen` in a loop condition; `strcat` in a loop | [hoist strlen](references/codegen.md#hoist-strlen-out-of-the-loop-condition), [end offset](references/memory.md#end-offset-instead-of-strcat) |
| Branch misses on random data | [branchless select](references/codegen.md#branchless-selection), [unconditional store](references/codegen.md#unconditional-store-with-select) |
| Cold error path in the hot loop | [branch hints](references/codegen.md#branch-probability-hints), [IR PGO](references/build-flags.md#ir-pgo) |
| Float reduction not vectorized (`fadd s`, no `fadd.4s`) | [pragma](references/build-flags.md#scoped-reassociation-pragma), [fast math](references/build-flags.md#fast-math), [NEON](references/codegen.md#neon-intrinsics) |
| Remark names a blocker the source cannot remove | [NEON](references/codegen.md#neon-intrinsics), [x86 dispatch](references/codegen.md#x86-runtime-dispatch) |
| Large array of small values | [narrow types](references/codegen.md#narrow-element-types) |
| `a + 1 < a`, overflow checks, size math | [signed overflow](references/codegen.md#signed-overflow-and-wraparound-types), [ckd_add](references/codegen.md#checked-arithmetic-with-ckd_add) |
| `sizeof` record larger than its fields | [member order](references/memory.md#struct-member-ordering) |
| Loop reads two fields of wide records | [struct of arrays](references/memory.md#struct-of-arrays) |
| Inner loop strides over rows | [loop order](references/memory.md#row-major-loop-order) |
| Hand copy, shift, or zero loops | [memcpy](references/memory.md#memcpy-for-non-overlapping-copies), [memmove](references/memory.md#memmove-for-overlapping-ranges), [memset](references/memory.md#memset-for-zeroing) |
| `memmove` per deleted element | [compaction](references/memory.md#single-pass-compaction) |
| One pass over data per key | [counting table](references/memory.md#direct-indexed-counting-table) |
| `malloc` per node, freed together | [arena](references/memory.md#arena-allocator) |
| `malloc`/`free` churn of one size | [free list](references/memory.md#free-list-of-fixed-size-slots) |
| `realloc` per push | [geometric growth](references/memory.md#geometric-growth-with-realloc) |
| Many small writes; `_IONBF`; `write` per record | [setvbuf](references/io.md#full-buffering-with-setvbuf), [line buffering](references/io.md#line-buffering), [batched write](references/io.md#batched-write-calls) |
| Hot call into another `.c` file | [full LTO](references/build-flags.md#full-lto), [ThinLTO](references/build-flags.md#thinlto), [static inline](references/build-flags.md#static-inline-functions-in-headers) |
| Branchy code, representative training input | [IR PGO](references/build-flags.md#ir-pgo), [front-end PGO](references/build-flags.md#front-end-pgo) |
| Release flags untouched | [O3](references/build-flags.md#optimization-level-o3), [target CPU](references/build-flags.md#target-cpu-native) |
| Shared library exports internals | [visibility](references/build-flags.md#hidden-visibility), [static](references/build-flags.md#static-internal-linkage) |

## Rules

- Measure optimized builds with the project's flags. Sanitizer and
  `-O0` builds answer correctness questions only.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric does not move: several cards record
  constructs that measured no difference or a slowdown.
- A candidate that does less work is invalid: skipped validation, a
  smaller input, a result the optimizer deleted (use the barrier and
  sink), or an error turned into a default.
- Undefined behavior invalidates any timing: signed overflow, aliasing
  that violates `restrict` or effective-type rules, out-of-bounds or
  overlapping `memcpy`, use after `realloc`, reads of freed arena
  memory. The oracle must run clean under ASan and UBSan.
- Preserve semantics a rewrite silently changes: float summation order
  and `-0.0`/NaN (fast math, reassociation, SIMD), stable element order
  (compaction), embedded `'\0'` in length-delimited data, output
  visibility timing (buffering), per-record durability (batched writes),
  and struct layout used as an ABI or file format.
- Flags such as `-mcpu`/`-march`, `-ffast-math`, LTO, PGO, and
  `-fvisibility` apply to the whole build and the deployment target.
  State the consequence and measure the application, not one loop.
- Before weakening an atomic memory order, state the synchronization and
  lifetime contract; fewer locks prove neither correctness nor less
  contention.
- Report only numbers you measured (with machine, compiler, and flags)
  or numbers from a linked primary source.

## Bundled tools

`assets/examples/verify.sh` copies the catalog to a temporary directory,
builds there with `CC`, `CSTD`, and `OPT` (defaults `cc`, `c17`, `-O2`),
and falls back to an installed macOS SDK that links when the default
does not:

- `verify` (default): oracles, allocator and write-call counts, C23
  `ckd_add` path, identical output from four emit variants.
- `benchmark`: every pair once; smoke only, no timing.
- `sanitize`: ASan+UBSan oracle run; requires UBSan to flag `ub.c`.
- `asm` and `remarks`: assert `-S` patterns and optimization records.
- `flags`: LTO call sites, visibility, target CPU, `-O3`, x86 dispatch.
- `pgo`: IR and front-end PGO pipelines, then hyperfine.
- `time [filter]`: timing loop medians plus hyperfine; `profile`:
  `leaks --atExit`, `sample`, `xctrace`.

The clang-only modes (`asm`, `remarks`, `flags`, `pgo`) print `NOT RUN`
for other compilers instead of passing.

## References

- [Measurement](references/measurement.md): timing loop, barrier,
  hyperfine, sanitizers, counting wrappers, remarks, records, `-S`,
  sample, xctrace, leaks, perf.
- [Build flags](references/build-flags.md): `-O3`, target CPU, LTO,
  ThinLTO, PGO, fast math, reassociation pragma, visibility, linkage.
- [Code generation](references/codegen.md): restrict, `strlen`,
  branchless, stores, hints, narrow types, NEON, dispatch, overflow.
- [Memory](references/memory.md): layout, SoA, loop order,
  `memcpy`/`memmove`/`memset`, joins, compaction, arena, free list,
  growth.
- [I/O](references/io.md): `setvbuf` modes and batched `write`.

## Completion evidence

The final report contains:

- `cc --version`, the full compile and link flags, OS and CPU;
- the profile, count, or codegen evidence that attributed the cost;
- the card applied and its preconditions checked;
- the oracle command and its result under ASan and UBSan;
- baseline and candidate numbers from the same machine and build, with
  units, repeats, and spread, plus the application-level result;
- every check not run (perf counters, other compilers or targets, the
  x86 path) stated as not verified.

[count]: references/measurement.md#counting-allocation-wrappers
