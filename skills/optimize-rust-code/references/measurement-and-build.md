# Profiling, Cargo profiles and PGO

Reviewed 2026-09-12 with Rust 1.98.1 on aarch64-apple-darwin. Verify the project
toolchain and target before applying version-specific guidance.

## Find the limiting resource

Build the actual workload with `cargo build --release --locked`, then profile
the produced executable with representative arguments. Use `cargo bench` for
workloads represented by that harness. Use `std::hint::black_box` to discourage
elimination of unused microbenchmark results. Supply representative inputs.

On Linux with perf available:

```sh
perf stat -r 5 -- ./target/release/analyzer fixtures/large.input
perf record -g --call-graph dwarf -- ./target/release/analyzer \
  fixtures/large.input
perf report
```

Replace the executable and fixture with the project's real ones. `stat` supplies
counters and repeated elapsed-time observations; `record` samples stacks.
Inspect inclusive and self costs before blaming a top-level caller. Missing
stacks can require symbols or a different unwinder. On macOS, record the release
executable with Instruments Time Profiler; use Allocations for allocation
questions. Resolve profiler access failures before interpreting results.
[Profiling methods](https://nnethercote.github.io/perf-book/profiling.html).

For allocation churn, use an existing DHAT/heaptrack or allocator-counting setup
to identify sites, sizes and lifetimes. High total allocation with little
retained memory suggests reuse; high retained capacity suggests lifetime/peak
sizing. Compare repeated before/after runs without profiling overhead. Record
rustc `-Vv`, target, flags, CPU, inputs, concurrency, errors and spread.
File-cache, turbo and thermal changes can exceed a small claimed win.
Performance gates need thresholds derived from observed variance and product
budgets, not a universal percentage on shared runners. Compare CPU, memory and
tail latency separately; a median improvement does not excuse worse tails.
Cross-language comparisons must match algorithms, numerical/error semantics,
allocator and security properties rather than attribute library differences to a
language.

## Build settings are tradeoffs

Define a separate profiling profile at the workspace root:

```toml
[profile.profiling]
inherits = "release"
debug = "line-tables-only"
strip = "none"
```

Build using `cargo build --profile profiling --locked`. Older Cargo versions may
need a supported debug value such as `1`. Profile configuration is read at the
workspace root. `opt-level=3` is not always faster than `2`; size modes can
reduce instruction-cache pressure but inhibit throughput optimizations.
`lto="thin"` and fewer codegen units trade build time for optimization
opportunities. Preserve panic and overflow behavior: `panic="abort"` changes
unwinding, and optimized arithmetic can differ when overflow checks are
disabled. Profile changes are experiments, not mandatory defaults.
[Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html).

## Reproducible PGO sequence

Use a fresh absolute directory and the compiler-matched `llvm-profdata`
(available through `llvm-tools-preview`; it is not automatically on PATH). For
rustup toolchains, locate it under
`$(rustc --print sysroot)/lib/rustlib/<host-triple>/bin/llvm-profdata`, using
the same toolchain for `rustc`, Cargo and the LLVM tools. A different compiler
installation on PATH can otherwise select an incompatible profile tool.

The following is an integration pattern for an existing Linux executable, not a
supplied analyzer program. Adapt the target, executable and training arguments:

```sh
pgo_case=$(mktemp -d)
RUSTFLAGS="-Cprofile-generate=$pgo_case" \
  cargo build --release --locked --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/release/analyzer fixtures/train.input
llvm-profdata merge -o "$pgo_case/merged.profdata" "$pgo_case"
RUSTFLAGS="-Cprofile-use=$pgo_case/merged.profdata \
-Cllvm-args=-pgo-warn-missing-function" \
  cargo build --release --locked --target x86_64-unknown-linux-gnu
```

Preserve any required existing RUSTFLAGS in **both** phases; the example assumes
none. Explicit `--target` prevents those flags instrumenting host build scripts.
Keep source, compiler, optimization and target flags consistent; train multiple
representative paths before merging. Missing-profile warnings can expose
untrained functions or stale data. Measure the final profile-use binary on
held-out inputs; instrumented timings are not the optimized result.
[rustc PGO](https://doc.rust-lang.org/rustc/profile-guided-optimization.html).

Refresh for a different compiler's LLVM profile format, unsupported profiler or
target architecture. Inspect
[ownership and concurrency](ownership-and-concurrency.md) before applying
layout, atomics or SIMD changes.

## Code size and build throughput

Measure clean builds, representative incremental `cargo check` or test builds,
release builds, and link time separately. `cargo build --timings` identifies
slow units and available parallelism. Large crates, proc macros, build scripts,
feature-heavy dependencies, monomorphization, linking, and production LTO/PGO
can affect different stages; do not split crates or change linkers without a
measured limiting stage. [Cargo build performance][source-4].

Runtime specialization and developer throughput trade off. Generics and
`impl Trait` can enable inlining and constant propagation but duplicate machine
code across concrete types. Coarse `dyn Trait` boundaries can reduce compile
work and instruction footprint but add indirect calls. Inspect artifact symbols
or linker output when code size or instruction-cache pressure is material.

### Splitting crates because the build feels slow

**Deciding condition:** Build performance is the requested outcome, but no
timing identifies crate scheduling or compilation as the limiting stage.

```text
Move every module into a separate crate so Cargo can compile everything in
parallel.
```

Why it fails:

- no timing identifies compilation as the limiting stage;
- crate boundaries add public contracts and can increase monomorphization or
  linking work;
- the change increases navigation and compatibility cost even if clean builds
  improve.

### Change the measured build bottleneck

```text
Evidence: cargo build --timings shows one proc-macro crate consumes 47% of clean
build time and serializes its dependents. Narrow its generated input and keep
the existing crate boundaries.
```

Why it works:

- the change targets an observed critical-path cost;
- it avoids unrelated public package boundaries;
- clean and representative incremental builds can verify the result.

Check:

- compare repeated clean and incremental timings with the same toolchain,
  target, features, and source state; run the full correctness checks too.

Measure shipped size and cold behavior for CLIs, plugins, serverless jobs, and
frequently restarted processes: on-disk bytes, mapped memory, page faults, time
to first useful result, initialization, and steady state. Size-oriented
`opt-level`, LTO, codegen units, stripping, and `panic = "abort"` change
separate costs and sometimes semantics. Cargo does not guarantee that
optimization level 3 is fastest or that `s`/`z` is smallest; compare the actual
artifact.
[Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html).

[source-4]: https://doc.rust-lang.org/cargo/guide/build-performance.html
