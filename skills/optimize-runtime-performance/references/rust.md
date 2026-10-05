# Rust Performance Gotchas

Benchmark with Criterion or `divan` (`cargo bench`), profile with
`samply record ./target/release/app` or `cargo flamegraph`, count allocations with DHAT (`dhat`
crate) or a counting `#[global_allocator]`, and read assembly with `cargo asm` (cargo-show-asm).
Debug builds are often 10 to 100 times slower and have a different hot spot, so use `--release` for
every measurement.

## Contents

- [Measurement](#measurement)
- [Allocation](#allocation)
- [Code Generation](#code-generation)
- [Build Profile](#build-profile)
- [Concurrency and I/O](#concurrency-and-io)

## Measurement

- Mistake: a benchmark whose result is unused or whose inputs are constants. Fix: wrap inputs and
  outputs in `std::hint::black_box`; `black_box` is best-effort and does not guarantee preventing
  optimization, so check the assembly when a result looks too good.
- Mistake: measuring setup or allocation of the input inside the timed closure. Fix: `iter_batched`
  (Criterion) or `with_inputs` (divan) so each iteration gets fresh input, such as a buffer that the
  function consumes or mutates.
- Mistake: believing a Criterion change report from one noisy run. Fix: compare against a saved
  baseline (`cargo bench -- --save-baseline before` and `--baseline before`), on an idle machine,
  and read the confidence interval, not the headline percentage.
- Mistake: profiling a stripped release binary. Fix: set
  `[profile.release] debug = "line-tables-only"` (or `debug = true`) for profiling runs; it adds
  symbols without changing code generation. Without frame pointers, unwinding can be lossy; build
  with `RUSTFLAGS="-C force-frame-pointers=yes"` for `perf`.
- Mistake: comparing with the wrong toolchain. Fix: record `rustc -Vv`, the target triple, and the
  profile; results differ across releases.

## Allocation

- Mistake: `collect::<Vec<_>>()` only to iterate again. Fix: stay lazy with iterator adaptors;
  collect only when the data is reused or the length is needed. Use `Vec::with_capacity(n)` when the
  length is known, and `extend` into a reused `Vec` (clear it, keep capacity).
- Mistake: `.to_string()`, `.clone()`, and `format!` inside a loop. Fix: borrow (`&str`,
  `Cow<'_, str>`), write into a reused `String` with `write!`, and intern keys once. Changing
  ownership changes lifetimes in public APIs, so keep the public signature unless asked.
- Mistake: `HashMap<String, V>` looked up with `.to_string()` keys. Fix: `map.get(key_str)` works
  with `&str` through `Borrow`; use the `entry` API once instead of `contains_key` followed by
  `insert`.
- Mistake: swapping in `FxHashMap` or `ahash` by default. Fix: they are faster for short trusted
  keys but not DoS-resistant; the std `SipHash` default exists for input from untrusted sources (a
  public service). Keep the default there unless the keys are trusted, and state it. Iteration order
  is unspecified in both, so output order must be sorted explicitly if observable.
- Mistake: `Box<dyn Trait>` per element in a hot collection. Fix: an enum, or generics
  (monomorphization), at the cost of code size; keep `dyn` where the set of types is open.
- Mistake: `Rc`/`Arc` clones in tight loops. Fix: pass `&T`; `Arc::clone` is an atomic increment and
  contended refcounts limit scaling.
- Mistake: `Vec<Vec<T>>` for a matrix. Fix: a flat `Vec<T>` with `row * cols + col`; fewer
  allocations and better locality.
- Mistake: `String` for bytes. Fix: `&[u8]` or `Vec<u8>` when the data is not guaranteed UTF-8 and
  parsing ASCII; validating UTF-8 costs a pass. Use `str::from_utf8` once, at the boundary.
- Mistake: `SmallVec` or `ArrayVec` everywhere. Fix: use them only where the profile shows
  allocation of small vectors; they increase moves and stack size.

## Code Generation

- Mistake: `get_unchecked` to remove bounds checks. Fix: first try iterators (`zip`, `chunks_exact`,
  `windows`) or slice hoisting (`let a = &a[..n];` before the loop); the compiler removes the checks
  when the length relation is visible. If the assembly still shows `panic_bounds_check` and the
  measured gain is real, use `unsafe` with a `SAFETY` comment, `debug_assert!` of the invariant, and
  a test. Out-of-bounds with `get_unchecked` is undefined behavior.
- Mistake: floating point sums written as a simple fold and expected to vectorize. Fix: floating
  point addition is not associative, so the compiler will not reorder it. Use several accumulators
  manually (this changes rounding), and keep results bit-identical only when the contract requires
  it; integer sums do vectorize.
- Mistake: `#[inline(always)]` sprinkled around. Fix: `#[inline]` is needed for cross-crate
  generic-free functions (otherwise not inlined without LTO); `inline(always)` can bloat code and
  slow it down. Move cold paths to a `#[cold]` `#[inline(never)]` function (error construction,
  panics) so the hot path is small.
- Mistake: `u32`/`usize` casts and overflow checks removed for speed. Fix: release builds wrap on
  overflow silently; decide between `wrapping_*`, `checked_*`, and `saturating_*` for correctness,
  and `overflow-checks = true` in the profile only if the cost is acceptable.
- Mistake: `println!` in a loop. Fix: it locks stdout, and Rust's stdout is always line-buffered, so
  every line is a write call. Wrap `stdout().lock()` in a `BufWriter`, write with `writeln!`, and
  flush at the end; handle `BrokenPipe` so the behavior of `| head` stays the same. Check that
  output bytes and exit code are identical.
- Mistake: reading a file line by line into new `String`s. Fix: `BufRead::read_line` into a reused
  `String` (clear it each time), or read the whole file and iterate `lines()` over the borrowed
  buffer. `lines()` strips `\r\n` and `\n`; check byte-level compatibility.
- Mistake: parsing numbers with `str::parse` in a hot loop with error conversions. Fix: measure
  first; specialized parsers (`atoi`-like, `lexical`, `fast-float`) exist, but check that they
  accept the same inputs (leading `+`, whitespace, overflow handling).

## Build Profile

- Mistake: copying `lto = "fat"`, `codegen-units = 1`, `panic = "abort"`, and `target-cpu=native`
  into a release profile together. Fix: apply each separately and measure. `lto` and
  `codegen-units = 1` cost build time; `panic = "abort"` removes unwinding, which breaks
  `catch_unwind`, test harnesses, and server code that relies on panics being caught per request;
  `target-cpu=native` produces binaries that fault with illegal instructions on older CPUs, so read
  the deploy notes (how and on which hardware it ships) before adding it. A portable level is
  `-C target-cpu=x86-64-v3` when the fleet supports it.
- Mistake: PGO or BOLT added without a training workload. Fix: `cargo pgo` needs a representative
  run and a rebuild per release; a stale profile pessimizes.
- Mistake: changing the allocator (`mimalloc`, `jemalloc`) for speed without an end-to-end
  measurement. Fix: benchmark the whole service, record RSS as well, and note that `jemalloc` is not
  supported on all targets.
- Mistake: `opt-level = 3` assumed best. Fix: `opt-level = 2` or `s` can be faster for
  code-size-sensitive workloads; measure.

## Concurrency and I/O

- Mistake: a `Mutex<HashMap>` updated per item by rayon workers. Fix: fold per-thread maps and
  `reduce` them (`par_iter().fold().reduce()`), or shard the map. Check that work units are large
  enough: rayon overhead exceeds gains for tiny items, so use `with_min_len`.
- Mistake: `std::sync::mpsc` or a `Mutex` per small item. Fix: batch the items; consider
  `crossbeam-channel` when measured.
- Mistake: blocking calls inside `async` tasks. Fix: `spawn_blocking` for CPU or blocking I/O; one
  blocked worker thread stalls every task scheduled on it.
- Mistake: unbuffered `File` reads and writes in small pieces. Fix: `BufReader`/`BufWriter`, or read
  in large chunks; a `BufWriter` dropped during a panic or `process::exit` may not flush, so flush
  explicitly before exit.
