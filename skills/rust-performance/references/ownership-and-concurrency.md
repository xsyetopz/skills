# Allocation, layout, unsafe and parallel work

Research: 2026-09-09; stable Rust 1.98.1 reference contracts. Use the project's
supported toolchain; nightly-only diagnostics or portable SIMD are optional
experiments, not prerequisites.

## Remove allocation at its owner

```rust
use std::io::{self, BufRead};
fn visit_lines<R: BufRead>(
    mut input: R,
    mut visit: impl FnMut(&str),
) -> io::Result<()> {
    let mut line = String::new();
    loop {
        line.clear();
        if input.read_line(&mut line)? == 0 { return Ok(()); }
        visit(&line);
    }
}
```

The loop reuses capacity and lends each line for the callback lifetime. It
preserves line terminators; stripping them would be a separate behavior change.
It can retain capacity after one huge line, so decide whether a measured memory
bound warrants replacing/shrinking the buffer. `Vec::with_capacity` avoids
growth when a reasonable size is known; overestimating every request can
increase peak memory. `clone_from` may reuse a destination allocation.
`Cow<str>` helps when most values remain borrowed but a minority require
ownership. [Allocation techniques][ref-1].

Prefer `&[T]` over `&Vec<T>` for read-only inputs. Borrowing removes copies but
couples lifetimes; owning a compact result can release a large input earlier.
`Arc::clone` increments an atomic count rather than cloning payload data, but
heavy cross-core count traffic can still matter. Do not introduce
`Arc<Mutex<_>>` where request-local ownership suffices.

## Layout follows access

Compare `size_of::<T>()` and allocation profiles before changing representation.
A large rarely-used enum variant can inflate every element; boxing that variant
reduces inline size at the cost of indirection/allocation. For a scan using only
positions, separate position storage may improve locality; for updates using
every field, array-of-structs can be simpler and faster. Preserve serialization
independently of Rust memory layout. Default Rust field layout is not a stable
ABI; `repr(C)` selects C layout rules but does not remove padding or make
arbitrary byte casts valid. [Type layout][ref-2].

## Unsafe boundary argument

For a safe wrapper around raw memory, state who owns the allocation; pointer
origin, alignment and validity; initialized length; bounds; aliasing;
destruction; and thread access. A `Vec` with capacity is not initialized
storage: setting length before initializing all elements can make reads/drop
undefined. For FFI, specify allocator and deallocator pairing, ABI, null/error
conventions and whether callbacks may outlive the call. Unwind and
partial-initialization paths must also preserve ownership. [Undefined
behavior][ref-3].

Prefer a checked slice operation until profiles establish bounds checks matter.
Miri can exercise unsafe paths with `cargo +nightly miri test` when the
repository permits that toolchain; unsupported FFI/OS paths and untested
executions remain outside its evidence. Review invariants beyond tested paths.
[Miri scope](https://github.com/rust-lang/miri).

## Atomics and contention

A metrics counter can use `AtomicU64::fetch_add(1, Ordering::Relaxed)` when it
does not publish or guard other memory. Publication requires a protocol: writes
before a Release operation become visible to a reader whose Acquire observes
that release (or its release sequence). Merely placing Acquire and Release
somewhere in two threads is insufficient. `SeqCst` adds a shared order for those
operations but does not repair invalid memory ownership. A compare-exchange
failure ordering cannot be Release or AcqRel. [Atomic model][ref-4],
[Ordering][ref-5].

Use a mutex for compound invariants. Shorten critical sections and measure
contention before replacing the lock. Shard only if keys distribute work; pad
hot per-thread counters only after identifying false sharing, because padding
expands memory. Bound queues, define whether cancellation discards queued work,
and avoid blocking an async executor with CPU loops. Make retried side effects
idempotent.

## SIMD and portable binaries

Prefer compiler vectorization first: contiguous slices, simple loops and
explicit aliasing through normal borrowing. Inspect optimized assembly with
`cargo rustc --release -- --emit=asm` for the relevant crate when useful. Stable
architecture intrinsics live under `std::arch`; `std::simd` remains a separate
feature-status decision. An x86 dispatch shape is:

```rust
fn process(bytes: &[u8]) {
    #[cfg(target_arch = "x86_64")]
    if std::is_x86_feature_detected!("avx2") {
        // SAFETY: this branch established the function's CPU requirement.
        unsafe { process_avx2(bytes) };
        return;
    }
    process_scalar(bytes);
}
```

`process_avx2` must be declared with `#[target_feature(enable = "avx2")]` and
implement valid loads, bounds and scalar tail handling; the dispatch check
establishes only CPU support. `process_scalar` is the required baseline.
`target-cpu=native` can bypass portability expectations and produce binaries
that fail on older machines. Test empty/short/misaligned input and tails as well
as large buffers; measure fallback and specialized paths. [Architecture
intrinsics and dispatch][ref-6].

[ref-1]: https://nnethercote.github.io/perf-book/heap-allocations.html
[ref-2]: https://doc.rust-lang.org/reference/type-layout.html
[ref-3]: https://doc.rust-lang.org/reference/behavior-considered-undefined.html
[ref-4]: https://doc.rust-lang.org/nomicon/atomics.html
[ref-5]: https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html
[ref-6]: https://doc.rust-lang.org/std/arch/index.html
