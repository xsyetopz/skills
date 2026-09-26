# Code-generation constructs

Cards that change the machine code of a hot loop or call: bounds checks,
vectorization, dispatch, inlining, and std algorithms. Pairs live in
[`constructs/src/codegen.rs`](../assets/examples/constructs/src/codegen.rs)
and [`dispatch.rs`](../assets/examples/constructs/src/dispatch.rs). The
oracle (`verify.sh verify`) proves equal results; `verify.sh asm` emits
release assembly with `-C codegen-units=1` and asserts the instruction
pattern each card claims, per `#[unsafe(no_mangle)]` symbol.

Measured numbers are machine-specific: Apple M1 Max, macOS arm64, rustc
1.98.1 (LLVM 22.1.8), default `release` profile. Times are medians from
`verify.sh time` unless marked Criterion, and read baseline -> candidate.
aarch64-only assertions (SIMD, `blr`, atomics) print `NOT ASSERTED` on
other architectures.

## Contents

- Iterators instead of indexing
- Reslice before the loop
- chunks_exact
- get_unchecked behind a checked invariant
- Independent accumulators for float auto-vectorization
- std::simd (nightly only)
- Generics instead of Box dyn Trait
- Enum dispatch for a closed set of types
- #[inline] across crates
- sort_unstable
- memchr-backed str search
- slice contains for bytes

## Iterators instead of indexing

**Definition.** Slice indexing `a[i]` is bounds-checked and panics when
out of range. Iterating (`iter()`, `zip`) yields elements without an
index, so no per-element check is emitted
([Performance Book][perf-bounds]).

**Use when.**

- The profile shows a hot indexed loop, and `--emit asm` shows
  `panic_bounds_check` in it.

**Do not use when.**

- `zip` would silently replace `a[i] * b[i]`: `zip` stops at the
  shorter slice where indexing panics. Keep the contract with an
  explicit length check (below), or document the change.
- The data is iterated twice: a consumed iterator yields nothing the
  second time. Collect first.
- An eager loop with side effects would become a lazy adapter that is
  never consumed: `map` runs its closure only when iterated.

**Example.**

```rust
pub fn dot_iter_candidate(a: &[u32], b: &[u32]) -> u32 {
    assert!(b.len() >= a.len(), "b shorter than a");
    a.iter()
        .zip(b)
        .fold(0u32, |sum, (&x, &y)| sum.wrapping_add(x.wrapping_mul(y)))
}
```

**Cost removed.** The per-element compare-and-branch. `verify.sh asm`:
`dot_index_baseline` 1 `panic_bounds_check`, candidate 0. Time did not
move: 280 -> 279 ns; Criterion `[276.09 279.51 286.52] ns` ->
`[275.34 275.51 275.70] ns` (4,096 elements), because the predictable
branch is nearly free on this CPU. Claim the assembly change; claim time
only when your own measurement shows it.

**Verify.**

1. Oracle compares lengths 0, 1, 3, 4,096 and checks both versions panic
   when `b` is shorter (under `panic = "unwind"`).
1. `sh assets/examples/verify.sh asm`.

## Reslice before the loop

**Definition.** `let src = &src[..dst.len()];` before the loop performs
one length check. Inside the loop LLVM then knows
`i < dst.len() == src.len()` and drops the per-element checks
([Performance Book][perf-bounds]).

**Use when.**

- An indexed loop reads several slices with the same index, and the
  body needs `i`, which makes iterators awkward.

**Do not use when.**

- The shorter slice is valid input: the reslice panics
  (`slice_end_index_len_fail`) where the original loop might have
  finished early for a different bound.

**Example.**

```rust
pub fn add_reslice_candidate(dst: &mut [u32], src: &[u32]) {
    let src = &src[..dst.len()];
    for i in 0..dst.len() {
        dst[i] = dst[i].wrapping_add(src[i]);
    }
}
```

**Cost removed.** `verify.sh asm`: `add_index_baseline` 1
`panic_bounds_check`, candidate 0. Time 594 -> 588 ns, within noise.

**Verify.**

1. Oracle compares `dst` after both versions for lengths 0-4,096.
1. `sh assets/examples/verify.sh asm`.

## chunks_exact

**Definition.** `slice::chunks_exact(n)` yields slices of exactly `n`
elements and leaves the tail to `.remainder()`; "the compiler can often
optimize the resulting code better than in the case of `chunks`"
([slice docs][slice]).

**Use when.**

- A loop steps by a fixed stride (`i += 4`) and indexes `i + k`.

**Do not use when.**

- The tail matters and `.remainder()` is not handled: its elements are
  silently skipped.

**Example.**

```rust
pub fn words_chunks_candidate(bytes: &[u8]) -> u32 {
    bytes.chunks_exact(4).fold(0u32, |sum, chunk| {
        let word = u32::from_le_bytes(chunk.try_into().expect("len 4"));
        sum.wrapping_add(word)
    })
}
```

**Cost removed.** `verify.sh asm`: `words_index_baseline` 4
`panic_bounds_check`, candidate 0. Time 1.431 µs -> 212 ns (about 18 KB
of input).

**Verify.**

1. Oracle compares lengths 0, 3, 4, 7, 4,001 (partial tails).
1. `sh assets/examples/verify.sh asm`.

## get_unchecked behind a checked invariant

**Definition.** `unsafe { slice.get_unchecked(i) }` skips the bounds
check; "calling this method with an out-of-bounds index is undefined
behavior even if the resulting reference is not used" ([slice][slice]).
The [Performance Book][perf-bounds] lists it as the last resort.

**Use when.**

- Safe forms (iterators, reslicing, `assert!`) do not remove the check,
  the assembly shows the check in the hot loop, and code you control
  establishes the bound: a constructor that validates every index into
  private, immutable fields.

**Do not use when.**

- The proof is "the caller always passes valid data": one bad input is
  memory corruption, not a panic.
- The invariant can change after validation (public fields, `&mut`
  access, a different `data` slice): re-check the length at entry.
- The code's tests cannot run under Miri (`cargo +nightly miri test`).
  Nightly was not installed, so Miri was not run for this example.

**Example.**

```rust
pub fn gather_unchecked_candidate(plan: &Gather, data: &[u32]) -> u32 {
    assert_eq!(data.len(), plan.source_len, "data length changed");
    plan.indices.iter().fold(0u32, |sum, &i| {
        // PERF/SAFETY: `Gather::new` proved every index < source_len, the
        // fields are private and immutable after construction, and the
        // assert above proves data.len() == source_len, so i < data.len().
        sum.wrapping_add(unsafe { *data.get_unchecked(i) })
    })
}
```

**Cost removed.** `verify.sh asm`: `gather_checked_baseline` 1
`panic_bounds_check`, candidate 0. Time 1.579 µs -> 829 ns (4,096
indices).

**Verify.**

1. Oracle compares results and checks `Gather::new` rejects an index
   equal to the length.
1. `sh assets/examples/verify.sh asm`; `rg -n 'get_unchecked' src/` and
   confirm each has a `// PERF/SAFETY:` comment naming the proof.

## Independent accumulators for float auto-vectorization

**Definition.** LLVM vectorizes loops whose iterations are independent.
A float sum is one serial dependency chain that LLVM must keep in IEEE
order, so it stays scalar. Accumulating into N independent lanes makes
each lane its own chain, which maps onto vector registers.

**Use when.**

- A hot `f32`/`f64` reduction (sum, dot product) shows scalar `fadd s`
  instructions in `--emit asm`.
- The caller accepts a different summation order.

**Do not use when.**

- Results must be bit-identical to the serial sum on arbitrary inputs:
  reassociation changes rounding. The oracle uses integer-valued inputs so
  every partial sum is exact.
- Lanes would start at `0.0`: since Rust 1.82, `Sum` for floats starts
  from `-0.0` ([PR 129321][float-sum]), so an empty-slice result would
  change from `-0.0` to `0.0`. The oracle caught exactly that; lanes
  start at `-0.0`.
- The reduction is over integers: LLVM already vectorizes it (wrapping
  add is associative).

**Example.**

```rust
pub fn sum_f32_candidate(values: &[f32]) -> f32 {
    let mut lanes = [-0.0f32; 8];
    let chunks = values.chunks_exact(8);
    let tail = chunks.remainder();
    for chunk in chunks {
        for (lane, &value) in lanes.iter_mut().zip(chunk) {
            *lane += value;
        }
    }
    lanes.iter().sum::<f32>() + tail.iter().sum::<f32>()
}
```

**Cost removed.** Scalar adds. `verify.sh asm` (aarch64): baseline 0
lines matching `fadd\.[0-9]+[hsd]` (vector form), candidate 5. Time
4.447 µs -> 510 ns; Criterion `[4.4542 4.4719 4.5077] µs` ->
`[518.14 525.01 536.69] ns` (4,096 values).

**Verify.**

1. Oracle compares `to_bits()` for lengths 0, 1, 7, 8, 9, 4,099.
1. `sh assets/examples/verify.sh asm`.

## std::simd (nightly only)

**Definition.** [`std::simd`][std-simd] provides portable vector types
(`f32x8`, ...) with lane-wise operators and reductions. It is
nightly-only and experimental, behind `#![feature(portable_simd)]`
(tracking issue 86656).

**Use when.**

- The project already builds on nightly and the auto-vectorizer does not
  produce the needed code.

**Do not use when.**

- The project uses stable Rust: it does not compile there. Use
  independent accumulators, `chunks_exact`, or `std::arch` intrinsics
  with `#[target_feature]`.

**Example.**

```rust
#![feature(portable_simd)]
use std::simd::f32x8;
use std::simd::num::SimdFloat;

fn sum_simd(values: &[f32]) -> f32 {
    let (chunks, tail) = values.as_chunks::<8>();
    let lanes = chunks
        .iter()
        .fold(f32x8::splat(-0.0), |acc, c| acc + f32x8::from_array(*c));
    lanes.reduce_sum() + tail.iter().sum::<f32>()
}
```

Runnable on nightly: `assets/examples/nightly/simd.rs`.

**Cost removed.** Same as the accumulator card, with explicit lanes.

**Verify.** Unexecuted: no nightly toolchain was installed. Run
`rustc +nightly -O --edition 2024 simd.rs && ./simd`; it asserts the
bits equal the serial sum.

## Generics instead of Box dyn Trait

**Definition.** A generic `fn f<S: Shape>(x: &[S])` is monomorphized:
one copy per concrete type, called with static dispatch. `Box<dyn Shape>`
calls through a vtable; the [Rust Book][book-dyn] notes dynamic dispatch
"prevents the compiler from choosing to inline a method's code".

**Use when.**

- A collection holds one concrete type at a time but is typed as
  `Vec<Box<dyn Trait>>`.

**Do not use when.**

- The collection is genuinely heterogeneous: use enum dispatch or keep
  `dyn`.
- Many instantiations would bloat code size and compile time: measure
  binary size.

**Example.**

```rust
pub fn total_generic<S: Shape>(shapes: &[S]) -> u64 {
    shapes.iter().map(Shape::area).sum()
}
// baseline: fn total_dyn(shapes: &[Box<dyn Shape>]) -> u64
```

**Cost removed.** One heap allocation and one indirect call per
element. Measured: `ALLOC generic-dispatch: 1025 -> 1` (building 1,024
shapes); `verify.sh asm` (aarch64): `total_dyn_baseline` 1 `blr`,
`total_generic_candidate` 0. Time 1.167 µs -> 387 ns.

**Verify.**

1. Oracle compares the totals.
1. `sh assets/examples/verify.sh asm` and the `ALLOC` line.

## Enum dispatch for a closed set of types

**Definition.** An `enum` with one variant per implementing type,
dispatched with `match`, stores values inline in one `Vec` and lets LLVM
inline each arm. For a closed, heterogeneous set it is the default over boxed
trait objects.

**Use when.**

- The set of types is closed (all in your crate) and the collection is
  heterogeneous.

**Do not use when.**

- Downstream crates must add types (plugins): an enum cannot be extended.
- Variants differ greatly in size: every element takes the largest
  variant's size; box the large variant.

**Example.**

```rust
pub enum AnyShape {
    Square(Square),
    Rect(Rect),
}

impl Shape for AnyShape {
    fn area(&self) -> u64 {
        match self {
            AnyShape::Square(s) => s.area(),
            AnyShape::Rect(r) => r.area(),
        }
    }
}
```

**Cost removed.** Measured: `ALLOC enum-dispatch: 1025 -> 1`;
`total_enum_candidate` 0 `blr`; time 2.121 µs -> 395 ns; Criterion
`[2.1140 2.1150 2.1161] µs` -> `[390.31 390.74 391.24] ns`.

**Verify.**

1. Oracle compares totals over a mix of both variants.
1. `sh assets/examples/verify.sh asm` and the `ALLOC` line.

## #[inline] across crates

**Definition.** `#[inline]` is a hint that makes a non-generic
function's body available to other crates so they can inline it
([Reference][ref-codegen]). Since Rust 1.75, rustc infers this for small
non-generic functions whose MIR has no calls or asserts
([PR 116505][pr-116505]), so the attribute matters for functions that
call something, including panic paths.

**Use when.**

- A small function in another crate of your workspace appears as a
  separate frame in the profile and as a `bl` in the caller's assembly.

**Do not use when.**

- The function is generic: generic bodies are already available to
  callers.
- The build uses thin or fat LTO: the attribute measured no gain there
  (baseline vs candidate 3.119 vs 3.092 µs thin, 3.108 vs 3.110 µs fat).
  Both LTO builds stayed slower than `#[inline]` under plain `release`
  (2.703 µs), so here LTO did not replace the attribute.
- The attribute would be `#[inline(always)]` by default: the Reference
  warns poor inlining decisions "can slow down programs".

**Example.**

```rust
// crate `helper`
#[inline]
pub fn scale_inline(x: u32) -> u32 {
    x.checked_mul(3).expect("scale overflow")
}
```

Runnable: `constructs/helper/src/lib.rs`, callers in `codegen.rs`.

**Cost removed.** One call per element. `verify.sh asm`:
`scale_all_baseline` 1 line referencing `helper[0-9]+scale` (the call
target), candidate 0. Time 4.600 -> 2.702 µs (4,096 values).

**Verify.**

1. Oracle compares results.
1. `sh assets/examples/verify.sh asm`.

## sort_unstable

**Definition.** `slice::sort` is stable and allocates auxiliary memory
for medium and large slices (driftsort). The `sort` docs state unstable
sorting "is generally faster than stable sorting and it doesn't allocate
auxiliary memory" ([alloc/src/slice.rs][sort-src]).

**Use when.**

- Equal elements are indistinguishable (primitives), or their relative
  order is not part of the output contract.

**Do not use when.**

- Sorting records by one key where ties must keep input order (for
  example "sort by date, keep submission order within a day"): the order
  of equal keys becomes unspecified.

**Example.**

```rust
pub fn sort_candidate(values: &mut [u32]) {
    // Equal u32 values are indistinguishable, so stability is unobservable.
    values.sort_unstable();
}
```

**Cost removed.** Measured: `ALLOC sort-unstable: 1 -> 0` (10,000 `u32`);
Criterion `[97.589 99.223 101.81] µs` -> `[82.761 82.970 83.183] µs`.

**Verify.**

1. Oracle compares the sorted outputs.
1. `ALLOC sort-unstable` line; `BENCH_FILTER=sort verify.sh measure`.

## memchr-backed str search

**Definition.** `str::find(char)`, `split_once(char)`, and similar
methods use a `CharSearcher` that calls `memchr` on the last UTF-8 byte
of the needle ([core/src/str/pattern.rs][pattern-src]). `&str` patterns
use the Two-Way searcher. The separate SIMD path for needles up to 32
bytes (x86_64 SSE2, aarch64 NEON) is reached only from
`is_contained_in`, that is `str::contains(&str)`, not from `find` or
`split_once`.

**Use when.**

- A hand-written `char_indices()` or byte loop searches for a delimiter.

**Do not use when.**

- The search is a predicate over characters, not a fixed char or
  string: `find(|c| ...)` works but has no `memchr` path.
- Byte offsets would be used as char counts: `find` returns byte
  indices.

**Example.**

```rust
pub fn split_key_candidate(line: &str) -> Option<(&str, &str)> {
    line.split_once(':')
}
```

**Cost removed.** Per-character decoding and comparison. Measured time
34 -> 11 ns for a 49-byte line with the colon near the end.

**Verify.**

1. Oracle compares `""`, `":"`, `"k:v"`, no colon, multi-byte text, and
   `"a::b"`.
1. `sh assets/examples/verify.sh time memchr`.

## slice contains for bytes

**Definition.** `<[T]>::contains` for one-byte `T` such as `u8` and `i8`
reinterprets the slice as bytes and calls `memchr`
([core/src/slice/cmp.rs][slice-cmp-src]).

**Use when.**

- Code tests for one byte value with `iter().any(|&b| b == x)` or a
  manual loop.

**Do not use when.**

- The position is needed: use `iter().position`, or the `memchr`
  crate if the dependency is allowed.

**Example.**

```rust
pub fn has_newline_candidate(bytes: &[u8]) -> bool {
    bytes.contains(&b'\n')
}
```

**Cost removed.** Measured time 14 -> 11 ns; the fixture finds a newline
within the first line, so the scan is short. Measure with your data.

**Verify.**

1. Oracle compares empty, one byte, newline only, and the fixture.
1. `sh assets/examples/verify.sh time memchr-contains`.

[perf-bounds]: https://nnethercote.github.io/perf-book/bounds-checks.html
[slice]: https://doc.rust-lang.org/std/primitive.slice.html
[float-sum]: https://github.com/rust-lang/rust/pull/129321
[std-simd]: https://doc.rust-lang.org/std/simd/index.html
[book-dyn]: https://doc.rust-lang.org/book/ch18-02-trait-objects.html
[ref-codegen]: https://doc.rust-lang.org/reference/attributes/codegen.html
[pr-116505]: https://github.com/rust-lang/rust/pull/116505
[sort-src]:
  https://github.com/rust-lang/rust/blob/master/library/alloc/src/slice.rs
[pattern-src]:
  https://github.com/rust-lang/rust/blob/master/library/core/src/str/pattern.rs
[slice-cmp-src]:
  https://github.com/rust-lang/rust/blob/master/library/core/src/slice/cmp.rs
