# Code generation constructs

Cards for source changes that alter the instructions the compiler
emits. Pairs are in
`assets/examples/constructs/codegen.c` unless noted. The oracle
`codegen_verify` compares baseline and candidate on edge inputs;
`verify.sh asm` and `verify.sh remarks` assert the instruction pattern or
optimization record each card names.

Measured results are machine-specific: Apple M1 Max, macOS arm64, Apple
clang 21.0.0 (swift.org toolchain), `-std=c17 -O2`, medians from
`sh assets/examples/verify.sh time` (21 batches), machine shared with
other builds (load average 8 to 60). Paired numbers come from separate
runs.

## Contents

- restrict pointers
- Hoist strlen out of the loop condition
- Branchless selection
- Unconditional store with select
- Branch probability hints
- Narrow element types
- NEON intrinsics
- x86 runtime dispatch
- Signed overflow and wraparound types
- Checked arithmetic with ckd_add

## restrict pointers

**Definition.** A `restrict`-qualified pointer parameter promises that,
during the function, every object accessed through it and modified is
accessed only through that pointer ([N3220][n3220] 6.7.4.2; N1570
6.7.3.1). The compiler may then keep loaded values in registers across
stores and drop run-time overlap checks.

**Use when.**

- Assembly shows a value reloaded after a store through another pointer.
- A copy or transform loop is vectorized with run-time overlap checks or
  is not turned into `memcpy`, and callers never pass overlapping
  ranges.

**Do not use when.**

- Any caller passes overlapping or identical pointers: the behavior is
  undefined and the optimized code reads stale values.
  `bump_plain(&y, &b, &y)` is valid for the plain version only.
- Measured time does not move: the vectorizer's run-time checks are
  cheap for long loops (see cost).

**Example.**

```c
NOINLINE void bump_plain(int *a, int *b, const int *x) {
  *a += *x;
  *b += *x; /* x may alias a: *x is loaded again */
}

NOINLINE void bump_restrict(int *restrict a, int *restrict b,
                            const int *restrict x) {
  *a += *x;
  *b += *x; /* one load of *x suffices */
}
```

**Cost removed.** Loads and overlap checks. Measured: `bump_plain: 4 ldr,
bump_restrict: 3 ldr`; `copy_restrict` becomes a tail call to `memcpy`,
`copy_plain` stays a vectorized loop with overlap checks. 1 MiB:
`restrict-copy` 22200 -> 19000 ns and 24000 -> 21450 ns;
`restrict-scale` 68050 -> 71950 ns and 97750 -> 88550 ns (no reliable
difference).

**Verify.**

1. Audit every call site for overlap. The oracle's aliasing call is
   legal only for the plain version.
1. `sh assets/examples/verify.sh asm` asserts fewer `ldr` in
   `bump_restrict` and `memcpy` in `copy_restrict` only.

## Hoist strlen out of the loop condition

**Definition.** Compute `strlen(s)` once before the loop instead of in
its condition. When the body may store into `s`, the compiler must
re-evaluate the condition every iteration, which makes the loop
quadratic.

**Use when.**

- The loop body writes through `s` or through a pointer that may alias
  it, and the profile shows `strlen` inside the loop.

**Do not use when.**

- The loop only reads `s`: clang already hoists the call (see cost), and
  the rewrite changes nothing measurable.
- The body can write `'\0'` or change the string's length: the hoisted
  length is then wrong.
- The data is length-delimited bytes that may contain `'\0'`: `strlen`
  stops at the first zero byte and truncates. Use the stored length.

**Example.**

```c
NOINLINE void upper_strlen_cond(char *s) {
  for (size_t i = 0; i < strlen(s); ++i) /* stores to s */
    s[i] = (char)toupper((unsigned char)s[i]);
}

NOINLINE void upper_hoisted(char *s) {
  size_t len = strlen(s); /* toupper never produces '\0' */
  for (size_t i = 0; i < len; ++i)
    s[i] = (char)toupper((unsigned char)s[i]);
}
```

**Cost removed.** One `strlen` per iteration. Measured, 16384-byte string:
`strlen-writes` 5753000 -> 26500 ns; read-only `strlen-readonly`
2900 -> 2900 ns (already hoisted: one `strlen` call site, loop
vectorized). The optimization record shows `!Analysis upper_strlen_cond
UnsupportedUncountableLoop`, absent for `upper_hoisted`.

**Verify.**

1. The oracle compares both versions on text with UTF-8 bytes.
1. `sh assets/examples/verify.sh remarks` asserts the uncountable-loop
   record for the baseline only.

## Branchless selection

**Definition.** Write a data-dependent choice as a conditional
expression on values (`base = x < key ? base + half : base`) in a loop
whose trip count does not depend on the comparison, so the compiler emits
a conditional select (`csel` on AArch64, `cmov` on x86-64) instead of a
branch.

**Use when.**

- The branch outcome is unpredictable (binary search over random keys,
  filtering random data) and branch misses dominate the profile.

**Do not use when.**

- The branch is predictable: a correctly predicted branch skips work the
  select always does.
- You assume the compiler keeps the branch: clang 21 already emitted
  `csel` in the branchy `lower_bound_branchy`. Check `-S` first.

**Example.**

```c
NOINLINE size_t lower_bound_branchless(const uint32_t *a, size_t n,
                                       uint32_t key) {
  if (n == 0)
    return 0;
  const uint32_t *base = a;
  while (n > 1) {
    size_t half = n / 2;
    base = base[half - 1] < key ? base + half : base; /* csel */
    n -= half;
  }
  return (size_t)(base - a) + (*base < key);
}
```

**Cost removed.** Measured, 4096 random keys over 2^20 sorted `uint32_t`:
`lower-bound` 252150 -> 203250, 322700 -> 247650, 311250 -> 226150,
289300 -> 210650 ns. Both versions contain one `csel`; the remaining
structural difference is that the candidate's loop count depends only on
`n`. Counters did not isolate the cause (no `perf` on macOS).

**Verify.**

1. The oracle compares both for every `n` in 0..257 and every key in
   0..390 over an array with duplicates.
1. `sh assets/examples/verify.sh asm` shows `csel` in both; on Linux,
   compare `perf stat -e branch-misses`.

## Unconditional store with select

**Definition.** Replace a conditional store (`if (a[i] < 0) a[i] =
0;`) with an unconditional store of a selected value (`a[i] = a[i] < 0 ?
0 : a[i];`). The loop becomes a plain vector max without masked stores.

**Use when.**

- The array is thread-private and writable, and a conditional store sits
  in a hot loop.

**Do not use when.**

- Other threads access elements the original never wrote: the new store
  adds a data race, which is why the compiler may not make this change
  itself.
- The memory is read-only or memory-mapped I/O.

**Example.**

```c
NOINLINE void clamp_branch(int32_t *a, size_t n) {
  for (size_t i = 0; i < n; ++i)
    if (a[i] < 0)
      a[i] = 0;
}

NOINLINE void clamp_select(int32_t *a, size_t n) {
  for (size_t i = 0; i < n; ++i)
    a[i] = a[i] < 0 ? 0 : a[i]; /* writes every element */
}
```

**Cost removed.** Per-lane branches. Measured, 2^20 random `int32_t` (both
timings include an identical 4 MiB restore copy): `clamp` 3766050 ->
157600 ns and 8802600 -> 364650 ns. Both loops are reported
`Vectorized 4`; only `clamp_select` contains `smax` (5 lines).

**Verify.**

1. The oracle compares both on random values including `INT32_MIN`.
1. `sh assets/examples/verify.sh asm` asserts `smax` in the candidate
   only.

## Branch probability hints

**Definition.** [`__builtin_expect(expr, val)`][clang-expect] tells the
compiler that `expr` is expected to equal `val`; it returns `expr` and
changes block layout, not semantics. [`__builtin_unpredictable`][clang-unpred]
marks a condition as unpredictable. ISO C has no standard equivalent.

**Use when.**

- A profile shows a cold error path laid out in the hot path, and a
  measurement with the hint shows a gain.

**Do not use when.**

- No measurement supports it: the measured pair showed no difference.
- The expectation is wrong for real input: layout then favors the rare
  path. Default to PGO, which measures the real frequencies.

**Example.**

```c
unsigned d = (unsigned)(unsigned char)s[i] - '0';
if (__builtin_expect(d > 9, 0))
  return -1; /* rare malformed input */
cur = cur * 10 + d;
```

**Cost removed.** None measured. 1 MiB of digits and commas:
`expect` 511850 -> 510450, 518500 -> 519900, 515550 -> 511250 ns.

**Verify.**

1. The oracle compares plain and hinted parsers, including the error
   path.
1. `sh assets/examples/verify.sh time expect` twice; keep the hint only
   when the difference exceeds the run-to-run spread.

## Narrow element types

**Definition.** Store values in the narrowest exact-width type that
holds their range (`uint8_t` instead of `int`; [N3220][n3220] 7.22.1.1)
so more elements fit per cache line and per vector register.

**Use when.**

- The working set exceeds a cache level and the loop is memory-bound.
- A table or record is stored in bulk (layout card).

**Do not use when.**

- The loop is compute-bound and must widen every element: the measured
  `uint8_t` count loop was slower.
- Arithmetic on the narrow type can exceed its range: operands promote
  to `int`, but the store truncates.

**Example.**

```c
NOINLINE uint32_t count_at_least_u8(const uint8_t *a, size_t n,
                                    uint8_t t) {
  uint32_t c = 0;
  for (size_t i = 0; i < n; ++i)
    c += a[i] >= t;
  return c;
}
```

**Cost removed.** Bytes: 1 MiB instead of 4 MiB for 2^20 elements; the
optimization record shows vector width 16 instead of 4. Measured time:
`narrow-type` 51200 -> 80100, 61750 -> 81500, 58100 -> 81500 ns (the
candidate was slower in every run).

**Verify.**

1. The oracle compares both counts on the same values.
1. `sh assets/examples/verify.sh remarks` asserts `Vectorized 4` and
   `Vectorized 16`; time on your data before keeping the change.

## NEON intrinsics

**Definition.** Functions from `<arm_neon.h>` that map to Advanced SIMD
instructions: `vld1q_f32` loads four floats, `vaddq_f32` adds lanes,
`vaddvq_f32` (AArch64 only) adds across lanes ([ACLE][acle-neon];
[Arm intrinsics][arm-intrinsics]). ACLE: "`__ARM_NEON` is always set to 1
for AArch64".

**Use when.**

- `-S` shows a hot loop not vectorized, remarks give a reason the source
  cannot remove, and the target is AArch64.

**Do not use when.**

- A pragma or source change already vectorizes the loop: the measured
  reassociation pragma beat this hand-written version.
- The code must build for other architectures without a portable
  fallback in the same file.

**Example.**

```c
NOINLINE float sum_f32_neon(const float *a, size_t n) {
  float32x4_t acc0 = vdupq_n_f32(0.0f), acc1 = vdupq_n_f32(0.0f);
  size_t i = 0;
  for (; i + 8 <= n; i += 8) {
    acc0 = vaddq_f32(acc0, vld1q_f32(a + i));
    acc1 = vaddq_f32(acc1, vld1q_f32(a + i + 4));
  }
  float s = vaddvq_f32(vaddq_f32(acc0, acc1)); /* horizontal add */
  for (; i < n; ++i)                            /* scalar tail */
    s += a[i];
  return s;
}
```

Guarded by `#if defined(__ARM_NEON) && defined(__aarch64__)` with a
scalar fallback.

**Cost removed.** Dependent scalar adds. Measured, 4096 floats:
`float-neon` 3828 -> 437 ns and 7476 -> 445 ns; the pragma candidate
measured 223 and 230 ns in the same runs. The summation order differs
from the scalar loop.

**Verify.**

1. The oracle checks every length 0..70 (tail handling) on exact inputs.
1. `sh assets/examples/verify.sh asm` asserts `fadd.4s` in
   `sum_f32_neon`.

## x86 runtime dispatch

**Definition.** Compile one function twice, once with
`__attribute__((target("avx2")))` ([clang target][clang-target]), and
choose at run time with [`__builtin_cpu_supports("avx2")`][gcc-x86],
so one binary uses AVX2 where available and still runs on older x86-64
CPUs. `__builtin_cpu_init()` is needed only in code that runs before
constructors.

**Use when.**

- One binary ships to x86-64 machines with different extensions and a
  hot loop benefits from the newer one.

**Do not use when.**

- The whole fleet has the extension: build with `-march=x86-64-v3`
  instead.
- The target is AArch64 and the extension is NEON: it is baseline.
  Dispatch only for optional features such as SVE.
- The hot inner loop would call the resolved pointer per element: the
  indirect call blocks inlining. Dispatch per batch.

**Example.**

```c
__attribute__((target("avx2"))) static uint32_t
sum_avx2(const uint32_t *a, size_t n) {
  uint32_t s = 0; /* same source; compiled with AVX2 enabled */
  for (size_t i = 0; i < n; ++i)
    s += a[i];
  return s;
}

static sum_fn pick_sum(void) {
  __builtin_cpu_init();
  return __builtin_cpu_supports("avx2") ? sum_avx2 : sum_portable;
}
```

Runnable: `assets/examples/flags/dispatch.c`.

**Cost removed.** Scalar or SSE-only code on AVX2 machines, without
losing older ones. Tier: **compiled** for x86-64 (`-target
x86_64-apple-macos11 -c`); not executed, because this host is arm64.
Measured: `nm dispatch-x86.o` lists `_sum_avx2`, `_sum_portable`, and
`___cpu_model`; the object has 8 lines with `ymm` registers. The arm64
build runs the portable path.

**Verify.**

1. On an x86-64 host, run the oracle with the AVX2 path forced off and
   on (swap the pointer) and compare results.
1. `sh assets/examples/verify.sh flags` prints the symbols of the
   cross-compiled object.

## Signed overflow and wraparound types

**Definition.** Signed integer overflow is undefined: "If an exceptional
condition occurs during the evaluation of an expression (that is, if the
result is not mathematically defined or not in the range of
representable values for its type), the behavior is undefined"
([N3220][n3220] 6.5.1p5; N1570 6.5p5). Unsigned arithmetic wraps modulo
2^N, so use exact-width unsigned types (`uint32_t`, `uint64_t`) for
intended wraparound (hashes, checksums, PRNGs).

**Use when.**

- A rewrite changes integer types, loop counters, or overflow checks.
- An overflow test is written as `a + 1 < a` on a signed type.

**Do not use when.**

- The only goal of converting a signed quantity to unsigned is to
  silence UBSan: the wrapped value is still wrong. Use a checked
  operation.

**Example.**

```c
__attribute__((noinline)) bool next_wraps_ub(int a) {
  return a + 1 < a; /* UB when a == INT_MAX */
}
```

Runnable: `assets/examples/flags/ub.c`; the FNV-1a hash in
`constructs/io.c` uses `uint64_t` for defined wraparound.

**Cost removed.** Silent wrong answers. Measured: `next_wraps_ub` compiles
to `mov w0, #0` and `ret` at `-O2`, printing `ub: 0` for `INT_MAX`;
`next_wraps_checked` prints `checked: 1`. Under UBSan:
`runtime error: signed integer overflow: 2147483647 + 1 cannot be
represented in type 'int'`.

**Verify.**

1. `sh assets/examples/verify.sh sanitize` requires the UBSan report.
1. `sh assets/examples/verify.sh asm` asserts the folded constant.

## Checked arithmetic with ckd_add

**Definition.** C23 `<stdckdint.h>` macros `ckd_add`, `ckd_sub`, and
`ckd_mul` compute the mathematical result, store it wrapped into
`*result`, and return `true` when it did not fit ([N3220][n3220] 7.20).
Before C23, clang and GCC provide `__builtin_add_overflow` with the same
contract ([GCC][gcc-overflow]).

**Use when.**

- Code has a hand-written overflow pre-check (`a > INT_MAX - b`) or an
  undefined post-check.
- A size calculation needs a check before allocation (`count * size`).

**Do not use when.**

- The project must build as C17 with a compiler lacking both: keep the
  pre-check.
- Operands are plain `char`, `bool`, or enumerations: the standard
  disallows them.

**Example.**

```c
#if __has_include(<stdckdint.h>) && __STDC_VERSION__ >= 202311L
#include <stdckdint.h>
#define CKD_ADD(r, a, b) ckd_add(r, a, b)
#else
#define CKD_ADD(r, a, b) __builtin_add_overflow(a, b, r)
#endif

NOINLINE bool sum_checked_ckd(const int *a, size_t n, int *out) {
  int s = 0;
  for (size_t i = 0; i < n; ++i)
    if (CKD_ADD(&s, s, a[i]))
      return false;
  *out = s;
  return true;
}
```

**Cost removed.** Compare-and-branch instructions. Measured: the loop body
of `sum_checked_ckd` is `ldr`, `adds`, `b.vs`, `subs`, `b.ne`; the
pre-check loop uses `eor`, `cmp`, `ccmp`, `tbz`, and a second `cmp`.
Not timed.

**Verify.**

1. The oracle checks in-range, `INT_MAX` overflow, and `INT_MIN`
   underflow; `verify.sh verify` runs it as C17 (`CKD path:
   __builtin_add_overflow`) and C23 (`CKD path: C23 ckd_add`).
1. `sh assets/examples/verify.sh asm` asserts `b.vs` in the candidate
   only.

[n3220]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf
[clang-expect]:
  https://clang.llvm.org/docs/LanguageExtensions.html#builtin-expect
[clang-unpred]:
  https://clang.llvm.org/docs/LanguageExtensions.html#builtin-unpredictable
[acle-neon]: https://arm-software.github.io/acle/main/acle.html#arm_neonh
[arm-intrinsics]:
  https://developer.arm.com/architectures/instruction-sets/intrinsics/
[clang-target]: https://clang.llvm.org/docs/AttributeReference.html#target
[gcc-x86]: https://gcc.gnu.org/onlinedocs/gcc/x86-Built-in-Functions.html
[gcc-overflow]:
  https://gcc.gnu.org/onlinedocs/gcc/Integer-Overflow-Builtins.html
