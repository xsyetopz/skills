# Build flag and linkage constructs

Cards for compiler and linker settings that change generated code
without source changes. A build setting reaches every translation unit
and the deployment target, so each card states that consequence.

Examples live in `assets/examples/flags/` and `constructs/`;
`sh assets/examples/verify.sh flags` and `pgo` run them in a temporary
directory. Measured results are machine-specific: Apple M1 Max, macOS arm64,
Apple clang 21.0.0 (swift.org toolchain), llvm-profdata from the same
toolchain, hyperfine 1.20.0, shared machine.

## Contents

- Optimization level O3
- Target CPU native
- Full LTO
- ThinLTO
- IR PGO
- Front-end PGO
- Fast math
- Scoped reassociation pragma
- Hidden visibility
- Static internal linkage
- Static inline functions in headers

## Optimization level O3

**Definition.** Clang's [`-O3`][clang-O] is "Like -O2, except that it
enables optimizations that take longer to perform or that may generate
larger code". `-O2` "enables most optimizations". GCC's `-O3` adds a
listed set of flags ([GCC -O3][gcc-O3]); the two compilers' lists differ.

**Use when.**

- The project ships `-O2`, a hot loop is measured, and a whole-program
  benchmark of the deployment build improves at `-O3`.

**Do not use when.**

- You assume `-O3` is faster: the measured catalog shows no consistent
  gain.
- Code size or instruction-cache pressure matters (embedded, large
  binaries): also measure size and cold-start time.
- You want `-Ofast` instead: it is deprecated since Clang 19, adds
  `-ffast-math`, and changes the results of correct code
  ([clang][clang-O]).

**Example.**

```sh
cc -std=c17 -O2 bench.c memory.c alloc.c codegen.c io.c main.c -o o2
cc -std=c17 -O3 bench.c memory.c alloc.c codegen.c io.c main.c -o o3
./o3 verify && wc -c o2 o3
./o2 time lower-bound && ./o3 time lower-bound
```

**Cost removed.** Possibly instructions in hot loops, paid for in code
size. Measured: binary 56880 bytes at `-O2`, 73408 at `-O3`; two runs each
of eight timed pairs showed differences inside the run-to-run spread
(`lower-bound` candidate 226150 and 210650 ns at `-O2`, 219700 and
220100 ns at `-O3`).

**Verify.**

1. `sh assets/examples/verify.sh flags` builds `-O3` and runs the oracle:
   `OPT-LEVEL binary bytes: -O2 56880, -O3 73408; -O3 passes verify`.
1. Compare `time` output for the hot pair and the whole-program
   hyperfine result; keep `-O2` if the intervals overlap.

## Target CPU native

**Definition.** `-mcpu=native` (AArch64) or `-march=native` (x86-64)
lets the compiler use every instruction extension of the build machine.
Clang's [`-march`][clang-march] allows instructions "valid on [that
processor family member] and later processors, but which may not exist
on earlier ones".

**Use when.**

- The binary runs only on the machine class that builds it (HPC node,
  local tool), and it needs vector extensions the default target lacks.

**Do not use when.**

- The binary is distributed: it can crash with an illegal instruction on
  older CPUs. Pick an explicit baseline (`-mcpu=apple-m1`,
  `-march=x86-64-v3`) or use runtime dispatch.
- You expect a change on Apple silicon with clang: the default target
  CPU is already `apple-m1`, and `-mcpu=native` and `-march=native` both
  resolve to `apple-m1` on this M1 Max.

**Example.**

```sh
cc -mcpu=native -### -c probe.c 2>&1 | grep -o '"-target-cpu" "[^"]*"'
cc -dM -E -x c /dev/null | sort >default.txt
cc -mcpu=apple-m4 -dM -E -x c /dev/null | sort >m4.txt
diff default.txt m4.txt   # features an M1 does not have
```

**Cost removed.** Instructions, when the default target lacks a needed
extension. Measured: `TARGET-CPU default: apple-m1`, `-mcpu=native:
apple-m1`, `-march=native: apple-m1` (no change). `-mcpu=apple-m4` adds
macros such as `__ARM_FEATURE_BF16`; this M1 Max reports
`hw.optional.arm.FEAT_BF16: 0` (`sysctl`).

**Verify.**

1. `sh assets/examples/verify.sh flags` prints the resolved target CPU
   for default, `-mcpu=native`, and `-march=native`.
1. Run the oracle on the oldest CPU the fleet supports, not only on the
   build machine.

## Full LTO

**Definition.** [`-flto`][clang-lto] (same as `-flto=full`) emits LLVM
bitcode objects. The linker merges all modules into one and optimizes
across translation units, so it can inline a call to a function defined
in another `.c` file.

**Use when.**

- The profile shows calls to small functions defined in other
  translation units inside hot loops.
- Release builds can afford a longer single-threaded link.

**Do not use when.**

- Link time or memory is the bottleneck: use ThinLTO.
- Objects must stay native code because the link step uses a linker or
  compiler that cannot read LLVM bitcode.
- On Darwin with `-g` and separate compile and link steps without
  `-Wl,-object_path_lto,<file>.o`: the ld64 linker deletes the LTO object
  needed for debugging ([clang][clang-lto]).

**Example.**

```c
/* lto_scale.c */
int lto_scale(int x) { return x * 3 + 1; }

/* lto_main.c: the hot loop calls across translation units. */
for (long i = 0; i < n; ++i)
  s += lto_scale((int)(i & 0xffff));
```

```sh
cc -O2 -flto lto_main.c lto_scale.c -o lto-full
otool -tv lto-full | grep -c 'bl.*_lto_scale'    # 0 when inlined
```

Runnable: `assets/examples/flags/lto_main.c`, `lto_scale.c`.

**Cost removed.** Call instructions and the optimizations they block.
Measured: `LTO none: 1 call site(s) to lto_scale`, `LTO full: 0`, same
output `1499500`.

**Verify.**

1. `sh assets/examples/verify.sh flags` compares the outputs of all
   three builds.
1. It asserts the call site count drops from at least 1 to 0.

## ThinLTO

**Definition.** [`-flto=thin`][thinlto] keeps per-module compilation and
imports only the summaries and function bodies that cross-module
inlining needs; the LLVM docs describe it as "both scalable and incremental".

**Use when.**

- A large project needs the cross-TU inlining of full LTO, or needs
  incremental and parallel link steps.

**Do not use when.**

- The toolchain's linker lacks ThinLTO support (non-LLVM linkers
  without the plugin): the link fails.

**Example.**

```sh
cc -O2 -flto=thin lto_main.c lto_scale.c -o lto-thin
otool -tv lto-thin | grep -c 'bl.*_lto_scale'
```

**Cost removed.** Same as full LTO. Measured: `LTO thin: 0 call site(s) to
lto_scale`, output identical.

**Verify.**

1. `sh assets/examples/verify.sh flags` asserts 0 call sites.
1. Time the real project's link with and without it; ThinLTO's benefit
   is build scalability.

## IR PGO

**Definition.** Profile-guided optimization with IR-level
instrumentation: build with `-fprofile-generate[=dir]`, run a
representative workload, merge the raw profiles with `llvm-profdata
merge`, rebuild with `-fprofile-use=file.profdata`. The clang manual
says "For best performance with PGO, IR-based instrumentation should be
used" ([clang PGO][clang-pgo]).

**Use when.**

- Branch-heavy or call-heavy code (parsers, interpreters, dispatch)
  where the compiler cannot know which paths are hot.
- A training workload exists that matches production input.

**Do not use when.**

- The training input is unrepresentative: the build then optimizes the
  wrong paths.
- `llvm-profdata` does not match the compiler version: a mismatched tool
  can fail to read or write the format. Use the one from the same
  toolchain (`xcrun --find llvm-profdata` follows `TOOLCHAINS`).
- The hot code is already branchless: the measured `classify` showed no
  reliable gain.

**Example.**

```sh
cc -O2 -fprofile-generate="$PWD/ir" pgo.c -o pgo-irgen
./pgo-irgen 20
llvm-profdata merge -o ir.profdata ir/*.profraw
cc -O2 -fprofile-use=ir.profdata -Werror=profile-instr-unprofiled \
  -Werror=profile-instr-out-of-date pgo.c -o pgo-ir
```

Runnable: `assets/examples/flags/pgo.c`; `verify.sh pgo`.

**Cost removed.** Mispredicted branches and poor block layout, when the
profile differs from the compiler's static guesses. Measured hyperfine,
`300` repetitions, shared machine: `pgo-base` 1.295 s ± 0.140 s (User
0.776 s), `pgo-ir` 956.3 ms ± 308.5 ms (User 0.745 s), `pgo-fe`
806.9 ms ± 119.7 ms (User 0.731 s). Second run: 1.224 s ± 0.722 s
(User 0.748 s), 1.016 s ± 0.434 s (User 0.745 s), 766.8 ms ± 21.7 ms
(User 0.733 s). The wall-time intervals overlap and user time differs by
about 2 percent: no reliable difference.

**Verify.**

1. `sh assets/examples/verify.sh pgo` asserts identical output from the
   base, IR-PGO, and front-end-PGO builds and prints
   `llvm-profdata show` (`Instrumentation level: IR`).
1. Run hyperfine on the base and PGO builds on a quiet machine; report
   no difference when the intervals overlap.

## Front-end PGO

**Definition.** Instrumentation inserted by clang's front end:
`-fprofile-instr-generate`, run with `LLVM_PROFILE_FILE="name-%p.profraw"`
(`%p` expands to the process ID; the default file is `default.profraw`),
merge with `llvm-profdata merge`, rebuild with
`-fprofile-instr-use=file.profdata`. It "has better source correlation,
so it should be used with source line-based coverage testing"
([clang PGO][clang-pgo]).

**Use when.**

- The same instrumented build also feeds source-based code coverage.

**Do not use when.**

- The only goal is speed: the manual recommends IR PGO for lower
  instrumentation overhead and better runtime performance.

**Example.**

```sh
cc -O2 -fprofile-instr-generate pgo.c -o pgo-fegen
LLVM_PROFILE_FILE="fe-%p.profraw" ./pgo-fegen 20
llvm-profdata merge -o fe.profdata fe-*.profraw
cc -O2 -fprofile-instr-use=fe.profdata pgo.c -o pgo-fe
```

**Cost removed.** As IR PGO; see the measured numbers there.

**Verify.**

1. `sh assets/examples/verify.sh pgo` builds and compares the outputs.
1. `llvm-profdata merge` is required even for one raw profile: "the
   merge operation also changes the file format".

## Fast math

**Definition.** [`-ffast-math`][clang-fast-math] lets the compiler treat
floating-point math as real-number algebra; it implies
`-fassociative-math`, `-freciprocal-math`, `-fno-signed-zeros`,
`-ffinite-math-only`, `-fno-honor-nans`, `-fno-honor-infinities`,
`-fno-math-errno`, `-ffp-contract=fast`, and more, and defines
`__FAST_MATH__`.

**Use when.**

- Every floating-point input and output of the translation unit is
  finite, results may change in the last bits, signed zero does not
  matter, the team agrees, and tests use tolerances.

**Do not use when.**

- The code produces or tests NaN or infinity: with finite-math this is
  undefined. Measured: clang 21 warned `use of NaN via a macro is undefined
  behavior due to the currently enabled floating-point options
  [-Wnan-infinity-disabled]`; that probe's `isnan` still returned 1, which
  the flags do not guarantee.
- Bitwise-reproducible results are required (golden files, consensus,
  tests comparing with `==`).
- Only one loop needs reassociation: use the scoped pragma.

**Example.**

```sh
cc -std=c17 -O2 -ffast-math -S codegen.c -o fm.s
awk '$1 == "_sum_f32_strict:" {on=1} on {print}
  on && /cfi_endproc/ {exit}' fm.s | grep -c 'fadd.4s'
```

**Cost removed.** The in-order reduction: measured, `sum_f32_strict` has 0
`fadd.4s` lines at `-O2` and 8 with `-ffast-math`.

**Verify.**

1. Run the oracle with tolerances or exact-integer inputs, plus a NaN,
   an infinity, and a `-0.0` case.
1. Count vector adds in the `-S` output as above.

## Scoped reassociation pragma

**Definition.** [`#pragma clang fp reassociate(on)`][clang-fp-pragma] at
the start of a compound statement allows floating-point reassociation
in that scope only, so a reduction can split into vector lanes.

**Use when.**

- One hot float reduction (`sum`, dot product) must vectorize and the
  rest of the file must keep strict IEEE semantics.

**Do not use when.**

- The result must be bit-identical to the sequential sum: the addition
  order changes, so rounding changes for general inputs.
- The compiler is not clang: GCC does not implement `#pragma clang`
  (it is an unknown pragma, reported by `-Wunknown-pragmas` under
  `-Wall`); use explicit accumulators or intrinsics there.

**Example.**

```c
NOINLINE float sum_f32_reassoc(const float *a, size_t n) {
#pragma clang fp reassociate(on)
  float s = 0.0f;
  for (size_t i = 0; i < n; ++i)
    s += a[i];
  return s;
}
```

Runnable: `assets/examples/constructs/codegen.c`.

**Cost removed.** Dependent scalar adds. Measured: `sum_f32_strict`
3863 ns and `sum_f32_reassoc` 223 ns for 4096 floats; assembly 0 versus
8 `fadd.4s` lines.

**Verify.**

1. The oracle compares sums on small-integer inputs, where every order
   gives the same bits; add a tolerance test for real data.
1. `sh assets/examples/verify.sh asm` asserts `fadd.4s` in the candidate
   and not in the baseline.

## Hidden visibility

**Definition.** [`-fvisibility=hidden`][gcc-vis] makes every symbol
hidden unless marked `__attribute__((visibility("default")))`, so a
shared library exports only its API. GCC: this "can very substantially
improve linking and load times of shared object libraries, produce more
optimized code, provide near-perfect API export and prevent symbol
clashes". On ELF, exported functions can be interposed, which blocks
inlining unless `-fno-semantic-interposition`
([GCC][gcc-interposition]).

**Use when.**

- A shared library's internal functions appear in `nm -gU` (Mach-O) or
  `nm -D` (ELF) output.

**Do not use when.**

- An ABI symbol lacks the default-visibility attribute: callers fail to
  link. Mark the API first.
- The build produces only a static executable: nothing is exported.

**Example.**

```c
#define API __attribute__((visibility("default")))

int vis_helper_a(int x) { return x * 2; }
int vis_helper_b(int x) { return x + 7; }
API int vis_api(int x) { return vis_helper_a(x) + vis_helper_b(x); }
```

```sh
cc -O2 -fvisibility=hidden -dynamiclib vis.c -o libvis.dylib
nm -gU libvis.dylib
```

Runnable: `assets/examples/flags/vis.c`.

**Cost removed.** Exported symbols (dynamic symbol table size, symbol
clashes, interposition barriers on ELF). Measured on Mach-O: `VISIBILITY
exported functions: default 3, hidden 1`. Both builds inlined the
helpers into `vis_api` (no `bl`), so no call was removed on Mach-O.

**Verify.**

1. Link a consumer against the library to prove the API still resolves.
1. `sh assets/examples/verify.sh flags` asserts fewer exported functions.

## Static internal linkage

**Definition.** A file-scope function declared `static` has internal
linkage: no other translation unit can call it, so the compiler can
drop its body once every call is inlined.

**Use when.**

- A helper is used only in its own `.c` file.

**Do not use when.**

- Another translation unit calls it: the link fails.
- You expect a speedup within one file: clang inlines small external
  functions too.

**Example.**

```c
int scale_extern(int x) { return x * 3 + 1; }
static int scale_static(int x) { return x * 3 + 1; }
```

Runnable: `assets/examples/constructs/codegen.c` (`apply_extern`,
`apply_static`).

**Cost removed.** Emitted code and exported symbols, not time. Measured:
`nm codegen.o` lists `scale_extern` but not `scale_static`; both
`apply_*` loops inline the helper (0 `bl _scale_extern`).

**Verify.**

1. The oracle compares `apply_extern` and `apply_static`.
1. `sh assets/examples/verify.sh asm` prints `NM codegen.o:
   scale_extern emitted, scale_static not emitted`.

## Static inline functions in headers

**Definition.** A `static inline` function defined in a header gives
each including translation unit its own internal-linkage copy, which
the compiler inlines and discards. A plain `inline` definition in C is an
"inline definition" that does not provide an external definition; one
translation unit must then supply an `extern` declaration, or calls that
are not inlined fail to link ([N3220][n3220] 6.7.5; N1570 6.7.4 for
C11/C17).

**Use when.**

- A small function (timing, bounds check, hash step) is used across many
  translation units and must inline without LTO.

**Do not use when.**

- The function is large: every translation unit may keep a copy, which
  grows code size.
- The function has static local state: each translation unit gets its
  own state.

**Example.**

```c
/* bench.h */
static inline uint64_t now_ns(void) {
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    abort();
  return (uint64_t)ts.tv_sec * UINT64_C(1000000000) +
         (uint64_t)ts.tv_nsec;
}
```

**Cost removed.** Call overhead across translation units without LTO.
Measured: `nm main.o` shows no `now_ns` at `-O2` (inlined everywhere) and a
local `t _now_ns` at `-O0`.

**Verify.**

1. `nm file.o | grep name` at the release optimization level is empty
   when every call was inlined.
1. The build links with and without optimization (the `-O0` build proves
   no missing external definition).

[clang-O]: https://clang.llvm.org/docs/CommandGuide/clang.html#cmdoption-O
[gcc-O3]: https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html#index-O3
[clang-march]:
  https://clang.llvm.org/docs/CommandGuide/clang.html#cmdoption-march
[clang-lto]:
  https://clang.llvm.org/docs/CommandGuide/clang.html#cmdoption-flto
[thinlto]: https://clang.llvm.org/docs/ThinLTO.html
[clang-pgo]:
  https://clang.llvm.org/docs/UsersManual.html#profiling-with-instrumentation
[clang-fast-math]:
  https://clang.llvm.org/docs/UsersManual.html#cmdoption-ffast-math
[clang-fp-pragma]:
  https://clang.llvm.org/docs/LanguageExtensions.html#extensions-to-specify-floating-point-flags
[gcc-vis]:
  https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html#index-fvisibility
[gcc-interposition]:
  https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html#index-fsemantic-interposition
[n3220]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf
