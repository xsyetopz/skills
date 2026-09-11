# Allocation, layout, unsafe and parallel work

Reviewed 2026-09-12 with Rust 1.98.1 on aarch64-apple-darwin. Verify the project
toolchain and target before applying version-specific guidance.

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
increase peak memory. Reserving for input length can waste substantial capacity
when most entries collapse to a few outputs; measure distinct-count distribution
and retained capacity, not only the fastest high-cardinality case. `clone_from`
may reuse a destination allocation. `Cow<str>` helps when most values remain
borrowed but a minority require ownership. [Allocation techniques][source-1].

Prefer `&[T]` over `&Vec<T>` for read-only inputs. Borrowing removes copies but
couples lifetimes; owning a compact result can release a large input earlier.
`Arc::clone` increments an atomic count rather than cloning payload data, but
heavy cross-core count traffic can still matter. Do not introduce
`Arc<Mutex<_>>` where request-local ownership suffices.

[source-1]: https://nnethercote.github.io/perf-book/heap-allocations.html

## Layout follows access

Compare `size_of::<T>()` and allocation profiles before changing representation.
A large rarely-used enum variant can inflate every element; boxing that variant
reduces inline size at the cost of indirection/allocation. For a scan using only
positions, separate position storage may improve locality; for updates using
every field, array-of-structs can be simpler and faster. Preserve serialization
independently of Rust memory layout. Default Rust field layout is not a stable
ABI; `repr(C)` selects C layout rules but does not remove padding or make
arbitrary byte casts valid.
[Type layout](https://doc.rust-lang.org/reference/type-layout.html).

Trait objects can reduce monomorphization but do not establish a stable plugin
ABI. For an actual binary boundary, specify compatible calling conventions, data
layout and ownership instead of exporting Rust trait-object internals. Changing
the global allocator is an application-level experiment: first locate allocation
churn, fragmentation or retention. Pools and arenas can retain peak memory
beyond useful lifetimes. [Allocator interfaces][alloc-source].

[alloc-source]: https://doc.rust-lang.org/std/alloc/

## Unsafe boundary argument

For a safe wrapper around raw memory, state who owns the allocation; pointer
origin, alignment and validity; initialized length; bounds; aliasing;
destruction; and thread access. A `Vec` with capacity is not initialized
storage: setting length before initializing all elements can make reads/drop
undefined. For FFI, specify allocator and deallocator pairing, ABI, null/error
conventions and whether callbacks may outlive the call. Unwind and
partial-initialization paths must also preserve ownership. [Undefined
behavior][source-3].

Prefer a checked slice operation until profiles establish bounds checks matter.
Miri can exercise unsafe paths with `cargo +nightly miri test` when the
repository permits that toolchain; unsupported FFI/OS paths and untested
executions remain outside its evidence. Review invariants beyond tested paths.
Rust does not yet have a complete formal unsafe semantics; experimental Miri
aliasing models are not normative guarantees. Pointer addresses alone do not
establish provenance. Prefer provenance-preserving pointer APIs over integer
round trips. Creating an invalid or unaligned reference can itself be undefined
behavior; do not create one merely to cast it to a raw pointer. `UnsafeCell`
permits interior mutation, not data races or overlapping unique references.
[Pointer contracts](https://doc.rust-lang.org/std/ptr/).

Exercise partial initialization, panic/drop paths, zero-length and offset
inputs. Where supported, differential fuzzing and native sanitizers complement
Miri; none replaces the safe-wrapper argument for every caller.
[Miri scope](https://github.com/rust-lang/miri).

[source-3]:
  https://doc.rust-lang.org/reference/behavior-considered-undefined.html

## Atomics and contention

A metrics counter can use `AtomicU64::fetch_add(1, Ordering::Relaxed)` when it
does not publish or guard other memory. Publication requires a protocol: writes
before a Release operation become visible to a reader whose Acquire observes
that release (or its release sequence). Merely placing Acquire and Release
somewhere in two threads is insufficient. `SeqCst` adds a shared order for those
operations but does not repair invalid memory ownership. A compare-exchange
failure ordering cannot be Release or AcqRel.
[Atomic model](https://doc.rust-lang.org/nomicon/atomics.html),
[Ordering](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html).

Use a mutex for compound invariants. Shorten critical sections and measure
contention before replacing the lock. Shard only if keys distribute work; pad
hot per-thread counters only after identifying false sharing, because padding
expands memory. Bound queues, define whether cancellation discards queued work,
and avoid blocking an async executor with CPU loops. Make retried side effects
idempotent.

## Runtime, I/O and collections

Choose collections from measured operations and access patterns. Prefer dense
arrays/slices or `Vec` for sequential data, `VecDeque` for front/back queues,
hash maps for keyed lookup, and ordered maps when order/ranges justify them. Use
`entry` to avoid repeated hash lookup. Use `sort_unstable` only when
equal-element order is irrelevant; internal sorting algorithm names are not API
contracts. [Slice sorting](https://doc.rust-lang.org/std/primitive.slice.html).

The default hash map includes collision resistance. A faster non-cryptographic
hasher can improve trusted-key workloads but can expose attacker-controlled maps
to collision denial of service. Preserve the input threat model while measuring.
[Hashing guidance](https://nnethercote.github.io/perf-book/hashing.html).

Keep byte-oriented protocols and delimiter scans on `&[u8]`; use `str` when
UTF-8 text semantics matter. Avoid repeated owned conversions and compiled regex
construction in hot paths. Batch small reads/writes or use buffered or vectored
I/O when latency and flush semantics allow it. Do not add a second buffer around
an already buffered boundary. [Standard I/O](https://doc.rust-lang.org/std/io/).

Async improves concurrency for wait-heavy work, not CPU throughput by itself.
Measure task count, wakeups, queue depth, allocation, worker utilization, and
tail latency. Keep blocking calls and long CPU loops off executor workers. For
Tokio, `spawn_blocking` uses a high blocking-thread limit; bound CPU work or use
a CPU-oriented pool rather than treating it as automatic CPU scheduling.
[Tokio tasks](https://docs.rs/tokio/latest/tokio/task/),
[`spawn_blocking`][source-5].

Release synchronous lock guards before `.await` unless the lock and runtime
contract explicitly permits suspension. Use bounded queues to make overload and
retained work visible. Account for cancellation at every await point and for
blocking work that cannot be stopped after it starts.

[source-5]: https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html

## SIMD and portable binaries

Prefer compiler vectorization first: contiguous slices, simple loops and
explicit aliasing through normal borrowing. Inspect optimized assembly with
`cargo rustc --release -- --emit=asm` for the relevant crate when useful. Stable
architecture intrinsics live under `std::arch`; `std::simd` remains a separate
feature-status decision. For x86 specializations, use `is_x86_feature_detected!`
in a safe dispatcher and isolate intrinsics in a function with the corresponding
`#[target_feature]`. Keep a baseline implementation for unsupported CPUs. CPU
detection establishes only feature support: the specialized function must also
prove load/store bounds, alignment and tail handling. Prefer an existing
maintained kernel library when it meets the required semantics rather than
inventing a SIMD layer. `target-cpu=native` can bypass portability expectations
and produce binaries that fail on older machines. Test empty/short/misaligned
input and tails as well as large buffers; measure fallback and specialized
paths. [Architecture intrinsics and dispatch][source-6].

[source-6]: https://doc.rust-lang.org/std/arch/index.html

## Numeric and device contracts

Reassociation can change floating-point results even when the mathematical
expression is equivalent. SIMD reductions can change accumulation order;
`mul_add` rounds once rather than twice. Use algebraic float operations only
when their relaxed guarantees satisfy the actual numerical contract. Test NaN,
infinities, signed zero and error tolerances where observable; do not call an
approximate reduction an exact drop-in replacement.
[Float operations](https://doc.rust-lang.org/std/primitive.f32.html).

For embedded targets, measure interrupt latency, stack/RAM/flash and device
throughput on hardware. `no_std` is a platform choice, not a speed guarantee.
Volatile access is not atomic synchronization. Prefer the target HAL's ownership
and DMA/cache contracts; desktop timing cannot validate them. [Volatile
semantics][volatile-source].

[volatile-source]: https://doc.rust-lang.org/std/ptr/fn.read_volatile.html
