# Measurement constructs

Cards for proving that a C change is equivalent and cheaper. The
runnable catalog is in `assets/examples/`; `verify.sh`
copies it to a temporary directory, so no binary, profile, or trace lands
in the skill.

Measured results in this file are machine-specific: Apple M1 Max, macOS
arm64, Apple clang 21.0.0 (swift.org toolchain selected by `TOOLCHAINS`),
default `-std=c17 -O2`, shared with other build jobs (load average 8 to
60 during runs). `perf` and Valgrind do not exist on this machine.

Toolchain note (machine-specific): linking with the default Command Line
Tools SDK failed with `ld: tapi error: malformed file ... libSystem.B.tbd
... unknown architecture arm64e.x1-macos`; compiling with `-c` worked.
`verify.sh` therefore links with the first SDK under
`/Library/Developer/CommandLineTools/SDKs` that links a trivial program
and prints the `SDKROOT` it used.

## Contents

- Monotonic clock timing loop
- Optimization barrier and result sink
- hyperfine for whole programs
- Sanitizer oracle build
- Counting allocation wrappers
- Optimization remarks
- Saved optimization records
- Assembly inspection
- sample
- xctrace Time Profiler
- leaks at exit
- Linux perf

## Monotonic clock timing loop

**Definition.** A loop that reads [`clock_gettime`][posix-clock] with
`CLOCK_MONOTONIC` before and after a batch of calls, divides by the batch
size, and reports the median of several batches. POSIX requires
`CLOCK_MONOTONIC`, and the clock "cannot be set", so wall-clock
adjustments do not distort intervals.

**Use when.**

- You compare two implementations of one function on prepared inputs
  inside one process.
- The project has no benchmark harness and must not gain a dependency.

**Do not use when.**

- One call is shorter than the clock resolution: `clock_getres` printed
  `1000 ns` here, so a 200 ns call timed alone reads 0 or 1000. Raise the
  batch size until one batch takes at least several milliseconds.
- The claim is about startup, I/O, or the whole program: use hyperfine.
- Inputs are built inside the timed batch: the time then includes setup.
  Build inputs first, as `memory_time` does.

**Example.**

```c
static inline uint64_t now_ns(void) {
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    abort();
  return (uint64_t)ts.tv_sec * UINT64_C(1000000000) +
         (uint64_t)ts.tv_nsec;
}

uint64_t bench_median_ns(bench_fn f, void *ctx, unsigned reps,
                         unsigned samples) {
  uint64_t per_call[64];
  for (unsigned s = 0; s < samples; ++s) {
    uint64_t start = now_ns();
    for (unsigned r = 0; r < reps; ++r)
      bench_sink += f(ctx); /* volatile sink keeps the result */
    per_call[s] = (now_ns() - start) / reps;
  }
  qsort(per_call, samples, sizeof per_call[0], cmp_u64);
  return per_call[samples / 2];
}
```

Runnable: `assets/examples/constructs/bench.h` and `bench.c`.

**Cost removed.** Measurement error, not runtime. The median of 21
batches resists outliers from other processes. Measured with
`sh assets/examples/verify.sh time`: `TIME expect baseline 511850 ns`
in one run and `1113350 ns` in another at load average 25, with the
candidate at 510450 and 520350 ns. So repeat runs and compare
baseline and candidate only within the same run.

**Verify.**

1. `sh assets/examples/verify.sh verify` passes before any timing; the
   harness does not check results.
1. `sh assets/examples/verify.sh time <filter>` prints `TIME` lines.
   Run it at least twice; differences smaller than the run-to-run spread
   are noise.

## Optimization barrier and result sink

**Definition.** An empty GNU C inline `asm` statement that takes a
pointer as input and clobbers `"memory"`, plus a `volatile` sink
variable. The compiler must assume the asm reads the pointed-to memory,
so stores before it survive, and it must perform every `volatile` write
([GCC extended asm][gcc-asm]).

**Use when.**

- The measured function writes memory the benchmark never reads (a
  copy into `dst`): without a barrier the stores are dead.
- A pure function is called in a loop with the same input: clang may
  call it once and reuse the result. For this reason `flags/pgo.c`
  needed a `__asm__ volatile("" : : : "memory")` inside its repetition
  loop.

**Do not use when.**

- The barrier would go inside the function under test: it blocks
  optimizations the production build performs.
- The compiler is MSVC: "Inline assembly is not supported on the ARM
  and x64 processors" ([MSVC docs][msvc-asm]); use a `volatile` sink or
  a function in a separate translation unit.

**Example.**

```c
static inline void escape(const void *p) {
  __asm__ volatile("" : : "r"(p) : "memory");
}

static uint64_t t_cmemcpy(void *c) {
  struct mem_ctx *m = c;
  copy_memcpy(m->dst, m->src, m->n);
  escape(m->dst); /* the copy is now observable */
  return m->dst[m->n - 1];
}
```

Runnable: `assets/examples/constructs/bench.h`, `memory.c`.

**Cost removed.** Measurement error: a deleted or hoisted call reports a
time no real call achieves. Measured: before the barrier was added,
`./pgo-base 300` ran 300 repetitions of a 1 MiB scan in 9.1 ms total
(the call was hoisted); after it, 1.295 s ± 0.140 s.

**Verify.**

1. Multiply the repetition count by 10: time must grow about 10 times.
1. `sh assets/examples/verify.sh asm` still finds the measured symbols
   in the `-S` output.

## hyperfine for whole programs

**Definition.** [hyperfine][hyperfine] runs each command repeatedly after
warm-up runs and reports mean, standard deviation, min, max, and relative
speed. `-N` runs without an intermediate shell; `--output=null` discards
the program's output; `--export-json` keeps raw times.

**Use when.**

- The claim is about process wall time: startup, I/O buffering, a CLI
  command, a PGO or LTO build.
- You compare two binaries on identical inputs.

**Do not use when.**

- The operation takes microseconds inside a larger process: process
  start dominates. Use the monotonic timing loop.
- The binaries differ in output: compare outputs first (`cksum`).

**Example.**

```sh
./cx emit-write 50000 | cksum
./cx emit-batched 50000 | cksum     # must match
hyperfine -N --warmup 3 --output=null \
  './cx emit-write 200000' './cx emit-batched 200000'
```

Runnable: `sh assets/examples/verify.sh time` (hyperfine 1.20.0).

**Cost removed.** Measurement error from single runs. Measured:
`emit-write 200000` 313.8 ms ± 30.3 ms (System 236.3 ms), `emit-batched`
27.0 ms ± 6.0 ms (System 1.8 ms), "11.62 ± 2.81 times faster".

**Verify.**

1. `verify.sh verify` prints `EMIT identical output from all four
   variants` before timing.
1. For a claimed win, the hyperfine summary interval (`± value`) must
   exclude 1.00; otherwise report no difference.

## Sanitizer oracle build

**Definition.** A build with `-fsanitize=address,undefined` that inserts
run-time checks: [AddressSanitizer][asan] detects out-of-bounds accesses,
use-after-free, double free, and more;
[UndefinedBehaviorSanitizer][ubsan] detects signed overflow, misaligned
access, invalid shifts, and more. `-fno-sanitize-recover=all` stops at
the first report.

**Use when.**

- An optimization touches pointers, bounds, lengths, aliasing, integer
  arithmetic, or lifetimes: run the oracle under sanitizers before
  measuring.

**Do not use when.**

- You measure speed: ASan's documented typical slowdown is 2x.
- You check leaks on macOS with `ASAN_OPTIONS=detect_leaks=1`: measured,
  it reported `120 byte(s) leaked in 3 allocation(s)` from libobjc and
  libxpc initializers, not from the program. Use `leaks -atExit`.
- You check unsigned wraparound: `unsigned-integer-overflow` is not part
  of `-fsanitize=undefined` because unsigned wraparound is defined.

**Example.**

```sh
cc -std=c17 -O1 -g -fno-omit-frame-pointer \
  -fsanitize=address,undefined -fno-sanitize-recover=all \
  bench.c memory.c alloc.c codegen.c io.c main.c -o cx-san
./cx-san verify
```

Runnable: `sh assets/examples/verify.sh sanitize`.

**Cost removed.** Undetected undefined behavior that makes a benchmark
invalid. Measured: the catalog's oracle passes with no report, and the
deliberate overflow in `flags/ub.c` stops with
`runtime error: signed integer overflow: 2147483647 + 1 cannot be
represented in type 'int'` and exit status 134.

**Verify.**

1. `sh assets/examples/verify.sh sanitize` prints
   `SANITIZE ASan+UBSan: verify passed with no report`.
1. The same mode requires the UBSan report from `flags/ub.c`, so a
   sanitizer that silently did nothing fails the script.

## Counting allocation wrappers

**Definition.** Functions `cm_malloc`, `cm_realloc`, and `cm_free`
increment counters and forward to the C library. Code under test
allocates through them, so the oracle can assert how many allocator
calls baseline and candidate make in the same run.

**Use when.**

- The claim is "fewer allocations" (arena, free list, growth policy).
- The code already routes allocation through a project allocator hook:
  count inside that hook.

**Do not use when.**

- The binaries or libraries cannot be modified: the wrappers need source
  changes. Use the Instruments Allocations template (see the xctrace
  card's tier note).
- You would redefine `malloc` with a macro: defining a reserved
  identifier as a macro name is undefined behavior ([N3220][n3220]
  6.4.2.1p9, 7.1.3).
- Several threads allocate: the counters are plain `unsigned long`. Use
  `_Atomic` counters.

**Example.**

```c
struct cm_counts cm;

void *cm_malloc(size_t size) {
  ++cm.mallocs;
  return malloc(size);
}

/* In the oracle: */
cm_reset();
uint64_t rb = list_malloc(n);
unsigned long base = cm.mallocs + cm.reallocs;
cm_reset();
uint64_t rc = list_arena(n);
check(rb == rc && cm.mallocs + cm.reallocs < base, "arena");
```

Runnable: `assets/examples/constructs/count.h`, `bench.c`, `alloc.c`.

**Cost removed.** Ambiguity: an allocation claim becomes a count. Measured:
`ALLOC arena baseline 5000 calls candidate 2 calls`.

**Verify.**

1. The oracle compares results and checks `cm.frees == cm.mallocs`.
1. `sh assets/examples/verify.sh verify` prints the `ALLOC` lines and
   fails when the candidate count is not lower.

## Optimization remarks

**Definition.** Clang's `-Rpass=<regex>` reports transformations a pass
made, `-Rpass-missed=<regex>` reports transformations it did not make,
and `-Rpass-analysis=<regex>` reports why ([clang manual][rpass];
[LLVM vectorizers][vectorizers]). The regex matches pass names such as
`loop-vectorize`, `slp-vectorizer`, `inline`, and `licm`.

**Use when.**

- A hot loop should vectorize, or a hot call should inline.
- You need to explain why a candidate did or did not change the
  generated code.

**Do not use when.**

- You treat "vectorized loop" as proof of speed: `sum_f32_strict` is
  reported `Vectorized` with width 4, yet its assembly has 21 scalar
  `fadd s` instructions and no `fadd.4s` (an in-order reduction).
- You grep all remarks for "vectorized": attribute each remark to a
  function (see saved optimization records) or a `file:line`.

**Example.**

```sh
cc -std=c17 -O2 -c codegen.c -o /dev/null \
  -Rpass-analysis=loop-vectorize 2>&1 | grep 'codegen.c:100'
```

Measured output for the `upper_strlen_cond` loop (strlen in the condition):

```text
codegen.c:100:3: remark: loop not vectorized: Cannot vectorize
uncountable loop [-Rpass-analysis=loop-vectorize]
codegen.c:100:3: remark: loop not vectorized: instruction cannot be
vectorized [-Rpass-analysis=loop-vectorize]
```

**Cost removed.** Guessing about what the compiler did. The remark names
the blocking reason, so the candidate targets it.

**Verify.**

1. `sh assets/examples/verify.sh remarks` prints `-Rpass-missed` lines
   for `codegen.c`.
1. The same mode asserts per-function records (next card).

## Saved optimization records

**Definition.** `-fsave-optimization-record` writes every remark to a
YAML file (`-foptimization-record-file=<path>` names it); each record
has a kind (`!Passed`, `!Missed`, `!Analysis`), `Pass`, `Name`,
`Function`, and arguments such as `VectorizationFactor`
([clang manual][opt-record]).

**Use when.**

- A script must assert a remark for one function (CI, `verify.sh`).
- You compare vector widths between baseline and candidate.

**Do not use when.**

- You read one loop interactively: `-Rpass-analysis` on stderr is
  shorter.

**Example.**

```sh
cc -std=c17 -O2 -c codegen.c -o codegen.o \
  -fsave-optimization-record -foptimization-record-file=cg.yaml
awk '/^--- !/{k=$2} /^Pass:/{p=$2} /^Name:/{n=$2}
     /^Function:/{f=$2}
     /^\.\.\./{if (p=="loop-vectorize") print k, f, n}' cg.yaml
```

**Cost removed.** Ambiguous attribution. Measured records include
`!Passed count_at_least_i32 Vectorized 4`,
`!Passed count_at_least_u8 Vectorized 16`, and
`!Analysis upper_strlen_cond UnsupportedUncountableLoop` (absent for
`upper_hoisted`).

**Verify.**

1. `sh assets/examples/verify.sh remarks` prints the record table.
1. It exits non-zero when an expected record is missing.

## Assembly inspection

**Definition.** `cc -S` writes the assembly of one translation unit.
Extract one function (Mach-O labels are `_name:`, ELF labels `name:`)
and count instruction patterns to turn a codegen claim into a number.

**Use when.**

- The claim is about instructions: a load removed (`restrict`), a branch
  replaced (`csel`), SIMD used (`fadd.4s`), a call inlined or turned
  into `memcpy`.

**Do not use when.**

- The functions are `static` and inlined: no label remains. Mark measured
  functions `__attribute__((noinline))` and give them external linkage.
- You compare across compilers or targets: patterns are
  target-specific, and `verify.sh asm` asserts register-level patterns
  only on aarch64.

**Example.**

```sh
cc -std=c17 -O2 -S codegen.c -o codegen.s
awk -v a="_bump_plain:" '$1 == a {on=1} on {print}
  on && /\.cfi_endproc/ {exit}' codegen.s | grep -c ldr
```

**Cost removed.** Speculation about codegen. Measured:
`bump_plain: 4 ldr, bump_restrict: 3 ldr`; `sum_f32_reassoc` 8 lines
with `fadd.4s`, `sum_f32_strict` 0.

**Verify.**

1. `sh assets/examples/verify.sh asm` prints one `ASM` line per
   assertion and `ASM PASSED`.
1. Baseline assertions were recorded with this compiler. When a newer
   compiler already fixes a baseline, the assertion fails and the card's
   construct is moot for that compiler.

## sample

**Definition.** macOS `sample(1)` (local manual: `man 1 sample`)
suspends a running process every 1 ms by default, records all thread
stacks, and prints a call tree with sample counts per frame (`sample PID
SECONDS -file out`).

**Use when.**

- A running process is slow and you need its hot frames without
  rebuilding or relaunching under a tracer.

**Do not use when.**

- The process ends before the sampling window does: use xctrace
  `--launch`.
- The binary lacks symbols: build with `-g` (keep `-O2`).
- System Integrity Protection or missing developer permissions refuse
  the attach; the script then reports "not verified".

**Example.**

```sh
./cx hot 4 &
sample $! 2 -file sample.txt
grep -m 3 -E 'strcat|join_strcat' sample.txt
```

**Cost removed.** Blind optimization. Measured (`verify.sh profile`):
`1249 join_strcat (in cx) + 36 memory.c:114` with `1179 strcat` beneath
it, the quadratic join that the end-offset card removes.

**Verify.**

1. The call tree names the function and source line you changed.
1. Re-sample the candidate: the frame's count drops or disappears.

## xctrace Time Profiler

**Definition.** `xctrace(1)` (`man 1 xctrace`, ships with Xcode) records
Instruments templates from the command line: `record --template 'Time
Profiler' --time-limit 3s --output t.trace --launch -- cmd` samples a
launched command, and `export --input t.trace --xpath ...` writes the
`time-profile` table as XML.

**Use when.**

- A short program must run under a sampling profiler from launch.
- A trace file must be opened later in Instruments.

**Do not use when.**

- Another profiling session holds the kernel profiler: one measured
  attempt failed with `_lockKPerf: could not lock kperf. Likely another
  session just started.` (exit 2); a retry minutes later succeeded.
- Xcode is not installed: xctrace ships with Xcode, not with the
  Command Line Tools.

**Example.**

```sh
xctrace record --template 'Time Profiler' --time-limit 3s \
  --output tp.trace --launch -- ./cx hot 2
xctrace export --input tp.trace --xpath \
  '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]'
```

**Cost removed.** Blind optimization. Measured (xctrace 16.0): the exported
table names `strcat`, `_platform_strlen`, and `join_strcat` frames.
Tier note: `--template Allocations --launch -- ./cx verify` failed here
with `Failed to attach to target process` (exit 2), so whole-program
allocation counts through Instruments are **not verified** on this
machine.

**Verify.**

1. `sh assets/examples/verify.sh profile` prints
   `XCTRACE: Time Profiler trace recorded` or the failure reason.
1. Compare the exported frames before and after the change.

## leaks at exit

**Definition.** `leaks -atExit -- cmd` (`man 1 leaks`) launches the command
and scans its heap for unreachable blocks when it exits; it sets
`MallocStackLogging=lite` so leaks show allocation stacks. Exit status 0
means no leaks, 1 means leaks, and greater than 1 means an error.

**Use when.**

- An allocation change (arena, free list, ownership move) must not leak.
- ASan's leak mode is noisy on macOS (see the sanitizer card).

**Do not use when.**

- The program keeps all memory reachable until exit (a global arena):
  leaks reports only unreachable blocks, not growth.
- You count allocator calls: `nodes malloced` in its output counts
  blocks alive at exit, not calls made. Use counting wrappers.

**Example.**

```sh
leaks -atExit -- ./cx verify | grep -E 'leaks? for|Process'
```

`verify.sh profile` spells the option `--atExit`; `leaks` accepted both
spellings here with the same `0 leaks` result.

**Cost removed.** Undetected leaks. Measured: `Process 21780: 0 leaks for 0
total leaked bytes.`; a probe that dropped one `malloc(100)` pointer
reported `1 leak for 112 total leaked bytes` with a `ROOT LEAK: <malloc
in main>` stack and exit status 1.

**Verify.**

1. `sh assets/examples/verify.sh profile` fails when leaks exits
   non-zero.
1. For growth rather than leaks, run `heap PID` or
   `MallocStackLogging=1` with `malloc_history` (`man 1 heap`,
   `man 1 malloc_history`).

## Linux perf

**Definition.** [`perf stat`][perf] counts hardware and software events
(cycles, instructions, branch misses, cache misses) for a command;
`perf record -g` samples call stacks and `perf report` shows them.

**Use when.**

- The target is Linux and the claim involves counters: branch misses for
  branchless code, cache misses for layout and loop order.

**Do not use when.**

- The host is macOS: perf does not exist there. Use sample and xctrace.
- A container or the `perf_event_paranoid` setting blocks events: they
  read `<not supported>`, which is not a zero count.

**Example.**

```sh
perf stat -e cycles,instructions,branch-misses -r 10 ./cx time lower
perf record -g ./cx hot 3 && perf report --stdio | head -40
```

**Cost removed.** Attribution by counter. Tier: **not runnable here**;
the commands were not executed on this machine.

**Verify.**

1. Run the commands on the Linux target; compare `branch-misses` between
   baseline and candidate builds.
1. Report the counters with the kernel version and CPU model.

[posix-clock]:
  https://pubs.opengroup.org/onlinepubs/9799919799/functions/clock_gettime.html
[gcc-asm]: https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html
[hyperfine]: https://github.com/sharkdp/hyperfine
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[ubsan]: https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
[rpass]: https://clang.llvm.org/docs/UsersManual.html#rpass
[vectorizers]: https://llvm.org/docs/Vectorizers.html
[opt-record]:
  https://clang.llvm.org/docs/UsersManual.html#opt-fsave-optimization-record
[msvc-asm]:
  https://learn.microsoft.com/en-us/cpp/assembler/inline/inline-assembler
[perf]: https://perfwiki.github.io/main/
[n3220]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf
