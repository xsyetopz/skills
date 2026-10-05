# C Performance Gotchas

Each item is a mistake that looks like an optimization, then the fix and the reason. Profile first
with `perf record -g ./prog` and `perf report`, `valgrind --tool=callgrind`, or `perf stat` for
counters (all Linux).

## Contents

- [Measurement](#measurement)
- [Memory and Allocation](#memory-and-allocation)
- [Aliasing and Codegen](#aliasing-and-codegen)
- [Build Flags](#build-flags)
- [I/O](#io)

## Measurement

- Mistake: timing a `-O0` build, or a `-O2` build whose loop result is unused. Fix: build with the
  production flags and make the result observable (write it to a `volatile` sink or print a
  checksum). The compiler deletes pure loops whose result is dead.
- Mistake: timing one run that includes page faults and cold caches. Fix: run at least 10 process
  runs with `perf stat -r 10` (Linux; reports mean ± stddev) and discard the first-touch run; page
  faults and file cache state dominate short runs.
- Mistake: trusting a profile built without frame pointers or debug info. Fix: build with
  `-g -fno-omit-frame-pointer` for profiling (`-g` does not change code generation), and use
  `perf record --call-graph dwarf` when the frame pointer is absent.
- Mistake: comparing builds at different optimization flags and calling the difference a source
  change. Fix: keep flags, compiler version, and linker identical between baseline and candidate.

## Memory and Allocation

- Mistake: replacing `malloc` per node with a hand-written freelist without measuring. Fix: look at
  `perf` for `malloc`/`free` share first; when `malloc`/`free` appear among the top profile entries,
  use an arena (one block, bump pointer, free all at once) and confirm lifetimes are really uniform,
  since an arena turns a leak or early free into silent corruption.
- Mistake: an arena that returns unaligned pointers. Fix: round every allocation up to
  `_Alignof(max_align_t)` or the type's alignment; misaligned access is undefined behavior and
  faults on some targets.
- Mistake: reordering struct fields for speed and breaking an ABI, on-disk, or wire format. Fix:
  check `offsetof`/`sizeof` users and serialization first; add `_Static_assert(sizeof(T) == N)`
  after the change. Sort fields by decreasing alignment to remove padding.
- Mistake: linked structures traversed in a hot loop (pointer chasing). Fix: a contiguous array of
  structs, or an array of indices, is often several times faster from cache behavior alone; confirm
  with `perf stat -e cache-misses` before and after.
- Mistake: array of structs when the loop reads one field. Fix: split into parallel arrays (struct
  of arrays) only for that hot loop, because it makes every other access site more awkward.
- Mistake: false sharing between per-thread counters in adjacent array slots. Fix: pad each to 64
  bytes (`alignas(64)`) or accumulate locally and merge at the end.

## Aliasing and Codegen

- Mistake: adding `restrict` to silence a missed vectorization. Fix: add it only where the pointers
  truly never overlap. Violating it is undefined behavior that may appear only at the next compiler
  version. Check the remark first (`clang -Rpass-missed=loop-vectorize`,
  `gcc -fopt-info-vec-missed`) to learn whether aliasing is the cause.
- Mistake: hand-unrolling or hand-vectorizing with intrinsics before reading the compiler report.
  Fix: read the vectorization report and the assembly (`objdump -d -M intel --no-show-raw-insn`, or
  `gcc -S`); a loop usually vectorizes once aliasing, a signed-overflow assumption, or a
  loop-carried dependency is fixed.
- Mistake: using `int` indexes on 64-bit targets in loops that also index arrays with `size_t`,
  forcing sign-extension and blocking transformations. Fix: use `size_t` (unsigned wraparound is
  defined, so it is not a substitute for a bounds check).
- Mistake: `inline` on a large function to force inlining. Fix: `inline` is a hint. Use
  `static inline` for header helpers, measure with `-Rpass=inline`, and use
  `__attribute__((always_inline))` only for tiny leaf functions.
- Mistake: replacing division or modulo with shifts by hand. Fix: the compiler does this for
  constants and power-of-two unsigned divisors. Do it by hand only for a divisor that is a runtime
  power of two, and assert that with a check.
- Mistake: `-ffast-math` for speed. Fix: it breaks NaN, infinity, and associativity guarantees
  program-wide and changes results. Use `-fno-math-errno` or `-fassociative-math` narrowly, or
  restructure the reduction with several accumulators, and compare outputs within a stated
  tolerance.
- Mistake: `-march=native` in a build shipped to other machines. Fix: pick a documented baseline
  (`-march=x86-64-v3`) or dispatch at runtime with `__builtin_cpu_supports`.

## Build Flags

- Mistake: enabling LTO and PGO together without checking the gain. Fix: measure each separately.
  PGO needs a representative training run; a profile from unrepresentative inputs slows the real
  workload.
- Mistake: benchmarking with sanitizers on. Fix: sanitizers (`-fsanitize=address,undefined`) are for
  the oracle run only, because they slow code several times and change its cost profile. Run the
  equivalence test under ASan and UBSan after every change, since an optimization that uses unsafe
  aliasing or an off-by-one often passes unsanitized.
- Mistake: `-O3` assumed faster than `-O2`. Fix: measure; larger code from unrolling and
  vectorization can lose to instruction-cache misses.

## I/O

- Mistake: `fgets` and `sscanf` per line for large inputs. Fix: read the whole file with one `fread`
  (or `mmap`), then parse in place with `strtol`/`strtod` over the buffer. `sscanf` re-parses its
  format string on every call.
- Mistake: `printf` per record to a pipe. Fix: a larger stdio buffer
  (`setvbuf(stdout, NULL, _IOFBF, 1 << 16)`) or build output in your own buffer and call `fwrite`
  once per chunk. Interleaving with `stderr` output changes when lines appear, so check who reads
  the stream.
- Mistake: `mmap` on a file that other processes truncate. Fix: a truncated mapping raises `SIGBUS`;
  use `read` for files you do not own.
- Mistake: `fsync` or `fflush` removed from a write loop for speed. Fix: keep them where durability
  is part of the contract; batch them instead.
