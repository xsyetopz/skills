# Measurement constructs

Cards for proving a Rust change is equivalent and cheaper: benchmark
harnesses, allocation counting, assembly inspection, and profilers. The
runnable catalog is [`assets/examples`](../assets/examples). `verify.sh`
copies it to a temporary directory and points `CARGO_TARGET_DIR` and
`CARGO_BUILD_BUILD_DIR` there, so no `target/` lands in the skill.

Measured numbers are machine-specific: Apple M1 Max, macOS arm64, rustc
1.98.1 (Homebrew, LLVM 22.1.8), criterion 0.8.2, hyperfine (installed),
and samply 0.13.1 (installed into a scratch directory). `perf` and
Valgrind are not available on macOS.

## Contents

- std::hint::black_box
- Std-only Instant harness
- Criterion benchmark
- Criterion saved baselines
- Criterion iter_batched for per-iteration setup
- hyperfine for whole-process comparisons
- Counting global allocator
- Counting wrappers for calls that are not allocations
- Assembly inspection with --emit asm
- samply
- cargo flamegraph
- Instruments and xctrace

## std::hint::black_box

**Definition.** [`std::hint::black_box`][black-box] (stable since 1.66)
is an identity function the optimizer is asked to treat as opaque, so a
benchmark input cannot be constant-folded and a result cannot be
deleted. The docs call it "best-effort": how much it blocks depends on
platform and backend, and correctness must not rely on it.

**Use when.**

- A benchmark passes literals or loop-invariant values into the measured
  function (`f(4096)` can be folded to a constant result).
- A benchmark discards the measured result (`let _ = f(x)` can be removed
  as dead code).

**Do not use when.**

- The value is inside the function under test: wrapping it there changes
  the measured code and blocks optimizations production code gets.
- The import is `criterion::black_box`: criterion 0.8.2 marks it
  `#[deprecated(note = "use std::hint::black_box() instead")]`
  (`src/lib.rs` line 164 of the published crate), although the docs.rs
  quickstart still imports it.

**Example.**

```rust
use std::hint::black_box;

group.bench_function("candidate", |b| {
    b.iter(|| a::squares_candidate(black_box(4096)))
});
```

Runnable: `assets/examples/ecosystem/benches/pairs.rs`; the std harness
black-boxes every result in `constructs/src/harness.rs`.

**Cost removed.** Measurement error, not runtime: a folded benchmark
reports a near-zero time that no real call achieves. To observe it,
remove `black_box` from an input; the time collapses or the function
symbol vanishes from `--emit asm` output.

**Verify.**

1. Every benchmark closure passes inputs through `black_box` and returns
   (or black-boxes) the result: `rg -n 'b.iter\(' benches/`.
1. `sh assets/examples/verify.sh asm` shows the measured functions still
   exist as symbols in the release assembly.

## Std-only Instant harness

**Definition.** A loop that runs the closure in fixed batches, divides
each batch's [`Instant`][instant] elapsed time by the batch size, and
reports the median and minimum. It needs no dependency and has no
outlier analysis, confidence interval, or change detection.

**Use when.**

- The project forbids new dev-dependencies or has no network for
  crates.
- A quick relative check is needed before writing a Criterion
  benchmark. Otherwise Criterion is the default.

**Do not use when.**

- The claim needs a confidence interval or regression detection: use
  Criterion.
- One batch is shorter than the timer resolution: raise `batch` until
  one batch takes well above the `Instant` resolution.

**Example.**

```rust
pub fn time<R>(samples: usize, batch: u32, mut f: impl FnMut() -> R)
    -> Timing
{
    for _ in 0..batch {
        black_box(f()); // warm-up batch
    }
    let mut per_call: Vec<Duration> = (0..samples)
        .map(|_| {
            let start = Instant::now();
            for _ in 0..batch {
                black_box(f());
            }
            start.elapsed() / batch
        })
        .collect();
    per_call.sort_unstable();
    Timing { median: per_call[samples / 2], min: per_call[0] }
}
```

Runnable: `assets/examples/constructs/src/harness.rs`.

**Cost removed.** A dependency and its build time. Measured with
`sh assets/examples/verify.sh time vectorize`:
`TIME vectorize baseline: median 4.447µs`, `candidate: median 510ns`.

**Verify.**

1. `sh assets/examples/verify.sh verify` passes before any timing (the
   harness never checks results).
1. `sh assets/examples/verify.sh time <filter>` prints a `TIME` line for
   baseline and candidate; repeat it and treat differences smaller than
   the run-to-run spread as noise.

## Criterion benchmark

**Definition.** [Criterion][criterion-docs] is a statistics-driven
benchmark library: it warms up, samples, fits the measurements, reports
a confidence interval (`time: [low estimate high]`), and compares with
the previous run. Benchmarks live in `benches/` with `harness = false`.

**Use when.**

- The project has, or allows, a dev-dependency for benchmarks.
- The result needs an interval and a comparison across runs.

**Do not use when.**

- The toolchain is older than criterion 0.8's `rust-version = "1.86"`
  (from its `Cargo.toml`); pin an older criterion or use the std harness.
- The claim is about process start-up or I/O of a whole binary: use
  hyperfine.

**Example.**

```toml
[dev-dependencies]
criterion = "0.8"

[[bench]]
name = "pairs"
harness = false
```

```rust
use criterion::{Criterion, criterion_group, criterion_main};
use std::hint::black_box;

fn allocation(c: &mut Criterion) {
    let mut group = c.benchmark_group("with-capacity");
    group.bench_function("baseline", |b| {
        b.iter(|| a::squares_baseline(black_box(4096)))
    });
    group.bench_function("candidate", |b| {
        b.iter(|| a::squares_candidate(black_box(4096)))
    });
    group.finish();
}

criterion_group!(benches, allocation);
criterion_main!(benches);
```

Runnable: `assets/examples/ecosystem/benches/pairs.rs`.

**Cost removed.** Guesswork about noise: the interval shows whether two
results overlap. Measured with `sh assets/examples/verify.sh measure`
(`--warm-up-time 1 --measurement-time 2`):
`with-capacity/baseline [3.2053 µs 3.2444 µs 3.3169 µs]`,
`with-capacity/candidate [1.9988 µs 2.0096 µs 2.0300 µs]`.

**Verify.**

1. Run the equivalence oracle first; Criterion does not compare outputs.
1. `cargo bench --bench pairs -- <filter>` (the filter is a regex over
   benchmark IDs per the [CLI options][criterion-cli]). A claimed
   improvement needs non-overlapping baseline and candidate intervals.

## Criterion saved baselines

**Definition.** `--save-baseline <name>` stores a run under a name;
`--baseline <name>` compares a later run against it without overwriting
([CLI options][criterion-cli]). Results live under `target/criterion`.

**Use when.**

- Baseline and candidate are two revisions of the same function (the same
  benchmark ID), not two functions in one build.

**Do not use when.**

- Toolchain, profile, `RUSTFLAGS`, or machine differ between the two
  runs: the comparison then measures the environment.
- `target/` is cleaned between runs: the baseline is deleted with it.

**Example.**

```sh
git switch main
cargo bench --bench pairs -- --save-baseline before
git switch perf-branch
cargo bench --bench pairs -- --baseline before
```

**Cost removed.** Manual transcription of numbers between revisions.
Measured with `--save-baseline before with-capacity`, then
`--baseline before with-capacity` on the *same* code
(`--warm-up-time 1 --measurement-time 2`): the candidate printed
`change: [−2.6330% +0.2260% +3.4840%] (p = 0.89 > 0.05)` and "No change
in performance detected", but the unchanged baseline printed
`change: [−17.256% −12.037% −7.2018%] (p = 0.00 < 0.05)` and
"Performance has improved". Short runs on a desktop produce significant
changes from noise alone.

**Verify.**

1. Both runs use the same `rustc -V`, profile, and flags (record them).
1. The candidate's `change:` interval excludes 0%, repeats in a second
   `--baseline` run, and an unchanged control benchmark in the same run
   shows no change.

## Criterion iter_batched for per-iteration setup

**Definition.** `iter_batched_ref(setup, routine, BatchSize)` runs
`setup` outside the timed region and passes `&mut` of its output to
`routine`, so input preparation (clone, allocation) is not timed.

**Use when.**

- The routine consumes or mutates its input (sorting, draining, in-place
  transforms) and needs a fresh copy each iteration.

**Do not use when.**

- The input is read-only: plain `iter` with a captured reference has
  less overhead.
- The setup cost is part of the operation being claimed.

**Example.**

```rust
group.bench_function("unstable", |b| {
    b.iter_batched_ref(
        || unsorted.clone(),
        |v| g::sort_candidate(v),
        BatchSize::SmallInput,
    )
});
```

Runnable: `sort` group in `assets/examples/ecosystem/benches/pairs.rs`.

**Cost removed.** The clone that would otherwise dominate a sort
benchmark. Measured: `sort/stable [97.589 µs 99.223 µs 101.81 µs]`,
`sort/unstable [82.761 µs 82.970 µs 83.183 µs]` (10,000 `u32`).

**Verify.**

1. The routine closure contains no `clone`/`collect` of the input:
   `rg -n 'iter_batched' -A4 benches/`.
1. `sh assets/examples/verify.sh measure` with `BENCH_FILTER=sort`.

## hyperfine for whole-process comparisons

**Definition.** [hyperfine][hyperfine] runs complete commands repeatedly
with warm-up runs and reports mean ± σ, min/max, and relative speed; `-N`
runs without an intermediate shell.

**Use when.**

- The cost is process-level: start-up, stdout/stderr writes, file I/O,
  or the whole application workload after a micro-level change.

**Do not use when.**

- The operation takes microseconds: process start-up dominates.
- Baseline and candidate cannot be selected by argument or binary path.

**Example.**

```sh
hyperfine --warmup 3 -N --output=null \
  'target/release/constructs print-baseline 200000' \
  'target/release/constructs print-candidate 200000' \
  'target/release/constructs print-buffered 200000'
```

Runnable: `sh assets/examples/verify.sh time` runs exactly this.

**Cost removed.** Unmeasured end-to-end effect. Measured:
`print-baseline 250.5 ms ± 7.9 ms`, `print-candidate 244.7 ms ± 2.4 ms`,
`print-buffered 8.7 ms ± 1.2 ms`. System time was about 210 ms for
`print-baseline` and `print-candidate`, and 1.4 ms for `print-buffered`.

**Verify.**

1. The commands produce identical output: `verify.sh verify` compares
   `cksum` of all three print modes.
1. hyperfine's summary line reports the candidate faster with a ± range
   that does not reach 1.00.

## Counting global allocator

**Definition.** A type implementing [`GlobalAlloc`][global-alloc] that
forwards to `std::alloc::System` and increments atomics in `alloc`,
`alloc_zeroed`, and `realloc`; registered with `#[global_allocator]` in a
binary, it counts every heap allocation call in the process.

**Use when.**

- The claim is "fewer allocations": unlike time, the count is
  deterministic for a given toolchain and input.
- A regression test must fail when allocations come back.

**Do not use when.**

- Tests run in parallel under libtest: other threads and output capture
  allocate into the same counters. Run the checks sequentially from a
  `main` (as `constructs verify` does) or with `--test-threads=1`.
- Only `alloc` is counted: `Vec`/`String` growth goes through
  `realloc`, so every growth step after the first is invisible.
- The assertion requires an allocation to happen: the `GlobalAlloc` docs
  state the optimizer may elide or move allocations, so assert
  "candidate < baseline" on measured values, never "baseline == N".

**Example.**

```rust
static CALLS: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for CountingAlloc {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        unsafe { System.alloc(layout) }
    }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        unsafe { System.realloc(p, l, n) }
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) {
        unsafe { System.dealloc(p, l) }
    }
    // alloc_zeroed counts the same way.
}

#[global_allocator]
static ALLOC: CountingAlloc = CountingAlloc;
```

Runnable: `constructs/src/alloc_count.rs`, registered in
`constructs/src/main.rs`; `check::fewer_allocations` warms up once, then
asserts `baseline > 0` and `candidate < baseline`.

**Cost removed.** Allocation calls, printed as
`ALLOC <card>: <baseline> -> <candidate> allocation calls`.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints one `ALLOC` line per
   allocation card and ends with `PASSED: <n> checks`.
1. Mutate a candidate (for example remove `with_capacity`) and confirm
   the check fails; a check that cannot fail proves nothing.

## Counting wrappers for calls that are not allocations

**Definition.** A wrapper type that implements the real resource's trait
(`Write`, `Read`, `BuildHasher`) and increments a counter on each call,
turning "fewer system calls" or "fewer hashes" into an exact number.

**Use when.**

- The construct removes calls to an expensive inner operation: writes to
  a file or socket, reads, hash computations.

**Do not use when.**

- The wrapper would change the inner behavior (short reads or writes
  the real resource would not do): it must forward exactly.

**Example.**

```rust
impl Write for CountingWriter {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.calls += 1;
        self.bytes.extend_from_slice(buf);
        Ok(buf.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
```

Runnable: `CountingWriter`, `CountingReader` in `constructs/src/io.rs`,
`CountingState` (counts `Hasher::finish`) in
`constructs/src/collections.rs`.

**Cost removed.** Measured oracle output:
`COUNT bufwriter: 3000 -> 1 inner write calls`,
`COUNT bufreader: 18615 -> 4 inner read calls`,
`COUNT entry-api: 11 -> 6 hash computations`.

**Verify.**

1. The oracle compares the produced bytes or results as well as counts.
1. `sh assets/examples/verify.sh verify` prints the `COUNT` lines.

## Assembly inspection with --emit asm

**Definition.** `cargo rustc --release --lib -- --emit asm` makes rustc
write assembly (`CRATE_NAME.s`, per the [command-line docs][rustc-emit])
next to the intermediate artifacts in `target/release/deps/`, or in the
configured [`build.build-dir`][build-dir] when one is set.
`-C codegen-units=1` yields one `.s` file per crate.

**Use when.**

- A card claims a bounds check, indirect call, atomic, or vector
  instruction was removed or added; the assembly proves it for this
  target without timing noise.

**Do not use when.**

- The function is generic and never instantiated in the crate: no code
  is emitted. Add a non-generic `#[unsafe(no_mangle)]` wrapper.
- The assembly comes from another target than the one claimed.

**Example.**

```sh
cargo rustc --release --lib -- --emit asm -C codegen-units=1
awk '$0=="_dot_iter_candidate:"{on=1} on{print}
     on&&/\.cfi_endproc/{exit}' target/release/deps/constructs-*.s \
  | grep -c panic_bounds_check
```

`#[unsafe(no_mangle)]` (edition 2024 spelling) keeps the symbol name
stable; macOS prefixes symbols with `_`. Runnable: `asm` mode of
`assets/examples/verify.sh`.

**Cost removed.** Bounds-check branches, indirect calls, atomic
read-modify-writes, or scalar loops, as counted instruction patterns.
The expectations were recorded with rustc 1.98.1 (LLVM 22) on aarch64.
The `panic_bounds_check` and helper-call counts were also confirmed on
`x86_64-unknown-linux-gnu` by emitting assembly with rustup's rustc
1.98.0 (not executed on x86 hardware). `cargo-show-asm` (`cargo asm`) is
an alternative; it was not installed or run.

**Verify.**

1. `sh assets/examples/verify.sh asm` fails with `symbol not found` if a
   function was renamed, so a missing symbol cannot pass silently.
1. Each `expect` line prints the match count; `ASM PASSED` ends the run.

## samply

**Definition.** [samply][samply] is a sampling CPU profiler for macOS,
Linux, and Windows; `samply record <cmd>` runs the command and opens the
profile in the Firefox Profiler. On macOS it needs no elevated
privileges for locally built binaries, which makes it the default
profiler there.

**Use when.**

- CPU time must be attributed to functions before choosing a card.
- The machine runs macOS, where `perf` does not exist.

**Do not use when.**

- The binary was built without symbols or line tables: use the
  `profiling` profile (see the build-profiles reference).
- The question is allocation attribution: count allocations
  instead.

**Example.**

```sh
cargo install --locked samply
cargo build --profile profiling
samply record ./target/profiling/constructs time
samply record --save-only --unstable-presymbolicate \
  -o prof.json.gz -- ./target/profiling/constructs time
```

**Cost removed.** Guessing the hot spot. Measured (samply 0.13.1,
second command): the saved profile contains 2,038 samples on the main
thread, and the `prof.json.syms.json` written by
`--unstable-presymbolicate` contains symbol names such as
`count_words_baseline`, `slice::sort::stable::driftsort_main`, and
`constructs::harness::time`.

**Verify.**

1. The hot functions in the profile are the ones the card changes.
1. After the change, record the same workload and confirm the changed
   function's share dropped.

## cargo flamegraph

**Definition.** [`cargo flamegraph`][flamegraph] builds the project and
renders a flame graph SVG from a profiler: `perf` on Linux. On macOS the
README says it uses `xctrace` and needs `--root`/sudo, while the
[Rust Performance Book][perf-book-profiling] lists it with DTrace
support. The sources disagree; check the installed version.

**Use when.**

- Review needs a single SVG artifact of a whole run.

**Do not use when.**

- Root is not allowed on the machine (macOS path).
- The release profile has no debug info: set
  `CARGO_PROFILE_RELEASE_DEBUG=true` as the README advises.

**Example.**

```sh
cargo install flamegraph
CARGO_PROFILE_RELEASE_DEBUG=true cargo flamegraph --root \
  --bin constructs -o flame.svg -- time
```

**Cost removed.** Same as samply: attribution before editing.

**Verify.** Unexecuted: `cargo-flamegraph` was not installed, and its
macOS path runs as root (`--root`), which the non-interactive session
could not grant.

## Instruments and xctrace

**Definition.** Apple's Instruments (Xcode) samples CPU time with the
Time Profiler template; `xctrace` is its command-line front end. The
[Rust Performance Book][perf-book-profiling] lists Instruments for
macOS.

**Use when.**

- Xcode is installed and the task needs Apple-specific counters or a
  GUI.

**Do not use when.**

- Only the Command Line Tools are installed: `xctrace` exits with
  "requires Xcode".

**Example.**

```sh
xctrace record --template 'Time Profiler' \
  --launch -- ./target/profiling/constructs time
```

**Cost removed.** Guessing the hot spot: the Time Profiler attributes
samples to functions before any edit.

**Verify.** Tier: **executed (recording)**. With Xcode 26.6 installed,
the command above (after `cargo build --profile profiling --bin
constructs`) exited 0 and saved a `Launch_constructs_<date>.trace`
bundle. `xctrace export --input <trace> --toc | grep -o
'schema="time-profile"'` printed `schema="time-profile"`. No hot-frame
claim is made from this recording.

[black-box]: https://doc.rust-lang.org/std/hint/fn.black_box.html
[instant]: https://doc.rust-lang.org/std/time/struct.Instant.html
[criterion-docs]: https://docs.rs/criterion/0.8.2/criterion/
[criterion-cli]:
  https://bheisler.github.io/criterion.rs/book/user_guide/command_line_options.html
[hyperfine]: https://github.com/sharkdp/hyperfine
[global-alloc]: https://doc.rust-lang.org/std/alloc/trait.GlobalAlloc.html
[rustc-emit]:
  https://doc.rust-lang.org/rustc/command-line-arguments.html#option-emit
[build-dir]: https://doc.rust-lang.org/cargo/reference/build-cache.html
[samply]: https://github.com/mstange/samply
[flamegraph]: https://github.com/flamegraph-rs/flamegraph
[perf-book-profiling]: https://nnethercote.github.io/perf-book/profiling.html
