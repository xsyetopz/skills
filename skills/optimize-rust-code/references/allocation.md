# Allocation constructs

Each card removes heap allocation calls from a measured hot path. Every
pair lives in [`allocation.rs`][allocation-rs]. The oracle in
`constructs/src/main.rs` checks equal results on edge inputs, then uses
the counting global allocator to assert that the baseline allocates and
the candidate allocates strictly less.

Measured numbers are machine-specific: Apple M1 Max, macOS arm64, rustc
1.98.1 (LLVM 22.1.8), default `release` profile. `ALLOC` counts come from
`sh assets/examples/verify.sh verify` (counts `alloc`, `alloc_zeroed`,
and `realloc`). Times are medians from `sh assets/examples/verify.sh time`
(std harness, 31 samples x 64 calls). Results read baseline -> candidate.

## Contents

- Vec::with_capacity
- reserve before extend_from_slice
- Reuse a buffer with clear
- Borrowed parameters instead of owned ones
- clone_from into an existing value
- Cow for conditional modification
- push_str into a presized String
- write! into a String instead of per-item format
- Fixed-size stack array instead of a scratch Vec
- Borrow instead of cloning an Arc
- Rc instead of Arc for single-threaded sharing

## Vec::with_capacity

**Definition.** [`Vec::with_capacity(n)`][vec] allocates room for at
least `n` elements up front, so pushes up to `n` never reallocate.
Without it the growth strategy is unspecified; the
[Performance Book][perf-heap] observed capacities 0, 4, 8, 16, ... at
the time of writing.

**Use when.**

- The final length, or a tight upper bound, is known before the loop
  (`input.len()`, a counted range, a header field).

**Do not use when.**

- The bound is untrusted input (a length prefix from the network):
  `with_capacity` panics above `isize::MAX` bytes and aborts the process
  when the allocation fails. Clamp the bound first.
- The bound is a loose over-estimate on a long-lived value: the unused
  capacity stays allocated because `Vec` never shrinks by itself.

**Example.**

```rust
pub fn squares_candidate(n: u64) -> Vec<u64> {
    let len = usize::try_from(n).expect("n fits in usize");
    let mut out = Vec::with_capacity(len);
    for i in 0..n {
        out.push(i * i);
    }
    out
}
```

**Cost removed.** Growth reallocations and their copies. Measured:
`ALLOC with-capacity: 9 -> 1` (n = 1000); time 3.197 -> 1.996 µs
(n = 4096); Criterion `[3.2053 3.2444 3.3169] µs` ->
`[1.9988 2.0096 2.0300] µs`.

**Verify.**

1. Oracle compares outputs for n = 0, 1, 4, 1000.
1. `ALLOC with-capacity` line shows the candidate at 1.

## reserve before extend_from_slice

**Definition.** `Vec::reserve(k)`/`reserve_exact(k)` guarantee capacity
`>= len + k` ([`Vec`][vec]); `extend_from_slice` then copies a whole
slice in one call instead of one `push` per element.

**Use when.**

- Several batches are appended and their total length is computable
  first (sum of `len()`).

**Do not use when.**

- `reserve_exact` would run repeatedly in a loop with small `k`: each
  call may reallocate to exactly the new size, defeating amortized
  growth. Use `reserve` there.

**Example.**

```rust
pub fn flatten_candidate(batches: &[Vec<u32>]) -> Vec<u32> {
    let total = batches.iter().map(Vec::len).sum();
    let mut out = Vec::new();
    out.reserve_exact(total);
    for batch in batches {
        out.extend_from_slice(batch);
    }
    out
}
```

**Cost removed.** Measured: `ALLOC reserve-extend: 10 -> 1`; time
1.866 µs -> 333 ns (64 batches of 0..63 elements).

**Verify.**

1. Oracle compares empty and non-empty batch lists.
1. `ALLOC reserve-extend` line.

## Reuse a buffer with clear

**Definition.** `Vec::clear` drops the elements but keeps the capacity;
"emptying a `Vec` and then filling it back up to the same `len` should
incur no calls to the allocator" ([`Vec` guarantees][vec]).

**Use when.**

- A temporary collection is created per loop iteration (per line, per
  request, per frame) and dropped at the end of it.

**Do not use when.**

- One outlier iteration grows the buffer huge and the loop is
  long-lived: the memory stays reserved. Call `shrink_to(limit)` after
  outliers.
- The buffer's contents must survive into the next iteration.

**Example.**

```rust
pub fn widest_candidate(text: &str) -> usize {
    let mut widest = 0;
    let mut fields: Vec<&str> = Vec::new();
    for line in text.lines() {
        fields.clear(); // keeps capacity from earlier lines
        fields.extend(line.split_whitespace());
        widest = widest.max(fields.len());
    }
    widest
}
```

**Cost removed.** Measured: `ALLOC clear-reuse: 1024 -> 2` (512 lines);
time 79.723 -> 35.276 µs.

**Verify.**

1. Oracle compares `""`, one word, blank lines, and the 512-line text.
1. `ALLOC clear-reuse` line.

## Borrowed parameters instead of owned ones

**Definition.** A function that only reads its input takes `&str` or
`&[T]` instead of `String` or `Vec<T>`, so callers that keep their value
no longer clone it.

**Use when.**

- The body only reads the argument, and call sites do `x.clone()` or
  `x.to_string()` to satisfy the signature.

**Do not use when.**

- The function stores the value (in a struct, a map, a channel): taking
  ownership avoids a second copy inside, and callers that are done with
  the value move it in for free.
- The signature is a public API you may not change: add a borrowing
  function and forward the owned one to it.

**Example.**

```rust
pub fn admins_baseline(names: Vec<String>) -> usize {
    names.iter().filter(|name| name.starts_with("admin")).count()
}

pub fn admins_candidate(names: &[String]) -> usize {
    names.iter().filter(|name| name.starts_with("admin")).count()
}
// baseline caller: admins_baseline(names.clone())
```

**Cost removed.** The caller's deep clone. Measured:
`ALLOC borrowed-params: 257 -> 0` (256 names); time 6.852 µs -> 184 ns.

**Verify.**

1. Oracle compares both on the same names.
1. `rg -n '\.clone\(\)|to_string\(\)|to_owned\(\)' src/` at the call
   sites shows the clones removed.

## clone_from into an existing value

**Definition.** `dst.clone_from(&src)` overwrites `dst` with a clone of
`src` and can reuse `dst`'s allocation
([Performance Book][perf-heap]).

**Use when.**

- A loop repeatedly replaces a long-lived `Vec`/`String` with a clone of
  similarly sized data (`last = frame.clone()`).

**Do not use when.**

- The destination is new each time: there is no allocation to reuse.
- A custom `Clone` impl does not override `clone_from`: the default is
  `*self = source.clone()`, which saves nothing.

**Example.**

```rust
let mut last = Vec::new();
for frame in frames {
    last.clone_from(frame); // reuses last's buffer
    total += last.len();
}
```

**Cost removed.** Measured: `ALLOC clone-from: 64 -> 1` (64 frames of
1 KiB); time 3.348 -> 1.042 µs.

**Verify.**

1. Oracle compares totals.
1. `ALLOC clone-from` line.

## Cow for conditional modification

**Definition.** [`Cow<'a, B>`][cow] holds either a borrow or an owned
value. Returning `Cow::Borrowed(input)` when nothing changes and
`Cow::Owned(modified)` otherwise allocates only on the modifying path.

**Use when.**

- Most inputs pass through unchanged (escaping, normalization,
  de-tabbing) and the result is consumed by reading.

**Do not use when.**

- Almost every input is modified: `Cow` adds a branch and a larger return
  type for no saving.
- Every caller immediately calls `.into_owned()` or `.to_string()`:
  the allocation only moves.

**Example.**

```rust
pub fn detab_candidate(line: &str) -> Cow<'_, str> {
    if line.contains('\t') {
        Cow::Owned(line.replace('\t', "    "))
    } else {
        Cow::Borrowed(line)
    }
}
```

**Cost removed.** Measured: `ALLOC cow: 1 -> 0` for a line without tabs;
time 42 -> 9 ns.

**Verify.**

1. Oracle compares `""`, no-tab, leading-tab, and multi-tab lines via
   `into_owned()`.
1. `ALLOC cow` line.

## push_str into a presized String

**Definition.** Compute the total from the pieces' lengths, then
`String::with_capacity(total)` and `push_str` append every piece into
one buffer.

**Use when.**

- A string is built from a known list of pieces in a loop
  (`out = out + part`, repeated `format!`).

**Do not use when.**

- A single `concat()`/`join(",")` call expresses the same result: it
  also presizes and is the default.
- The pieces need formatting (numbers, `Display`): use `write!`.

**Example.**

```rust
pub fn join_candidate(parts: &[&str]) -> String {
    let len = parts.iter().map(|part| part.len() + 1).sum();
    let mut out = String::with_capacity(len);
    for part in parts {
        out.push_str(part);
        out.push(',');
    }
    out
}
```

**Cost removed.** Growth reallocations (`String + &str` reuses the left
buffer but still grows it). Measured: `ALLOC push-str: 9 -> 1`; time
1.822 -> 1.330 µs (256 parts).

**Verify.**

1. Oracle compares empty and 256-part inputs.
1. `ALLOC push-str` line.

## write! into a String instead of per-item format

**Definition.** `String` implements `std::fmt::Write`, so
`write!(out, ...)` formats directly into the existing buffer, while
`format!` allocates a new `String` per call.

**Use when.**

- A loop does `out.push_str(&format!(...))` or collects `format!` results
  only to join them.

**Do not use when.**

- The output goes to an `io::Write` sink (file, socket, stdout): write
  there directly instead of building a `String` first.
- The import is `io::Write` instead of `use std::fmt::Write as _;`: the
  call does not compile for `String`.

**Example.**

```rust
use std::fmt::Write as _;

pub fn render_candidate(pairs: &[(&str, u32)]) -> String {
    let mut out = String::new();
    for (key, value) in pairs {
        write!(out, "{key}={value};").expect("String write is infallible");
    }
    out
}
```

**Cost removed.** One temporary `String` per item. Measured:
`ALLOC write-macro: 71 -> 7` (64 pairs; the 7 are the output's growth);
time 4.712 -> 2.259 µs.

**Verify.**

1. Oracle compares the rendered strings.
1. `ALLOC write-macro` line.

## Fixed-size stack array instead of a scratch Vec

**Definition.** A `[T; N]` local with a separate length lives in the
stack frame. When `N` is a proven upper bound, it replaces a heap `Vec`
scratch buffer without allocating.

**Use when.**

- The maximum size is a small compile-time constant derived from the type
  (`u64` has at most 20 decimal digits; a SHA-256 digest is 32 bytes).

**Do not use when.**

- The bound comes from input: an index past `N` panics, and a large `N`
  risks stack overflow, especially on threads with small stacks.
- The data must outlive the function: return the array by value or use a
  `Vec`.

**Example.**

```rust
pub fn digits_candidate(n: u64) -> u64 {
    // u64::MAX has 20 decimal digits, so 20 bytes always suffice.
    let mut digits = [0u8; 20];
    let mut len = 0;
    let mut rest = n;
    loop {
        digits[len] = (rest % 10) as u8;
        len += 1;
        rest /= 10;
        if rest == 0 {
            break;
        }
    }
    digits[..len].iter().rev().fold(0, |acc, &d| acc * 31 + u64::from(d))
}
```

**Cost removed.** Measured: `ALLOC stack-array: 3 -> 0` for `u64::MAX`;
time 124 -> 29 ns. `SmallVec`/`ArrayVec` (crates) cover the "usually
small, sometimes large" case; they are not used here.

**Verify.**

1. Oracle compares 0, 7, 10, 1,234,567,890, and `u64::MAX`.
1. `ALLOC stack-array` line.

## Borrow instead of cloning an Arc

**Definition.** `Arc::clone` increments an atomic reference count and
the drop decrements it; "atomic operations are more expensive than
ordinary memory accesses" ([`Arc`][arc]). Passing `&T` (or `&[T]`) to a
call that does not keep the value avoids both.

**Use when.**

- A function takes `Arc<T>` but only reads it during the call, and hot
  call sites write `Arc::clone(&x)` to satisfy it.

**Do not use when.**

- The callee stores the handle or moves it to another thread/task: it
  needs ownership (`'static` for `thread::spawn`).
- Changing the signature breaks a public API you may not change.

**Example.**

```rust
fn sum_owned_arc(values: Arc<Vec<u64>>) -> u64 {
    values.iter().sum()
}
fn sum_borrowed(values: &[u64]) -> u64 {
    values.iter().sum()
}
// baseline: sum_owned_arc(Arc::clone(shared))
// candidate: sum_borrowed(shared)
```

**Cost removed.** One atomic increment and one atomic decrement per call.
`verify.sh asm` (aarch64): `arc_clone_baseline` has 1 line matching
`ldadd|ldxr|stlxr|cas`, `arc_borrow_candidate` 0. The local time
(5.456 µs -> 91 ns, 64 calls on 1,024 elements) is not evidence for the
atomics alone: without the refcount side effect, the candidate's
loop-invariant read-only call can be hoisted out of the loop. Claim the
assembly difference and time the real workload.

**Verify.**

1. Oracle compares sums and checks `Arc::strong_count` is back to 1.
1. `sh assets/examples/verify.sh asm` asserts the atomic is gone.

## Rc instead of Arc for single-threaded sharing

**Definition.** `Rc<T>` counts references with ordinary memory
operations; `Arc<T>` uses atomics. The [`Arc` docs][arc] say: "If you are
not sharing reference-counted allocations between threads, consider
using `Rc<T>` for lower overhead."

**Use when.**

- The shared value never crosses a thread boundary. The compiler
  enforces this: `Rc` is not `Send`.

**Do not use when.**

- The type must be `Send`/`Sync` (thread pools, `tokio::spawn`, rayon):
  it will not compile, and working around it with `unsafe` is unsound.
- A library API promises `Arc` for its callers' flexibility.

**Example.**

```rust
pub fn handles_rc_candidate(n: usize) -> usize {
    let root = Rc::new(7u64);
    let handles: Vec<Rc<u64>> = (0..n).map(|_| Rc::clone(&root)).collect();
    let count = Rc::strong_count(&root);
    drop(handles);
    count
}
```

**Cost removed.** Atomic read-modify-writes. `verify.sh asm` (aarch64):
`handles_arc_baseline` 4 atomic lines, `handles_rc_candidate` 0.
Measured time 11.011 -> 5.106 µs (1,024 handles).

**Verify.**

1. Oracle compares the strong counts.
1. `sh assets/examples/verify.sh asm`.

[vec]: https://doc.rust-lang.org/std/vec/struct.Vec.html
[perf-heap]: https://nnethercote.github.io/perf-book/heap-allocations.html
[cow]: https://doc.rust-lang.org/std/borrow/enum.Cow.html
[arc]: https://doc.rust-lang.org/std/sync/struct.Arc.html
[allocation-rs]: ../assets/examples/constructs/src/allocation.rs
