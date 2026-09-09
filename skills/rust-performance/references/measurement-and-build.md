# Profiling, Cargo profiles and PGO

Research: 2026-09-09. Latest stable examined: **Rust 1.98.1**, whose [release
note][ref-1] reports a vtable miscompilation fix.

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
[Profiling methods][ref-2].

For allocation churn, use an existing DHAT/heaptrack or allocator-counting setup
to identify sites, sizes and lifetimes. High total allocation with little
retained memory suggests reuse; high retained capacity suggests lifetime/peak
sizing. Compare repeated before/after runs without profiling overhead. Record
rustc `-Vv`, target, flags, CPU, inputs, concurrency, errors and spread.
File-cache, turbo and thermal changes can exceed a small claimed win.

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
disabled. Profile changes are experiments, not mandatory defaults. [Cargo
profiles][ref-3].

## Reproducible PGO sequence

Use a fresh absolute directory and the compiler-matched `llvm-profdata`
(available through `llvm-tools-preview`; it is not automatically on PATH).
Example for an existing Linux target, adapting the binary and arguments:

```sh
pgo_case=$(mktemp -d)
RUSTFLAGS="-Cprofile-generate=$pgo_case" cargo build --release --target \
  x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/release/analyzer fixtures/train.input
llvm-profdata merge -o "$pgo_case/merged.profdata" "$pgo_case"
RUSTFLAGS="-Cprofile-use=$pgo_case/merged.profdata \
-Cllvm-args=-pgo-warn-missing-function" \
  cargo build --release --target x86_64-unknown-linux-gnu
```

Preserve any required existing RUSTFLAGS in **both** phases; the example assumes
none. Explicit `--target` prevents those flags instrumenting host build scripts.
Keep source, compiler, optimization and target flags consistent; train multiple
representative paths before merging. Missing-profile warnings can expose
untrained functions or stale data. Measure the final profile-use binary on
held-out inputs; instrumented timings are not the optimized result. [rustc
PGO][ref-4].

Refresh for a different compiler's LLVM profile format, unsupported profiler or
target architecture. Inspect [ownership and concurrency][ref-5] before applying
layout, atomics or SIMD changes.

[ref-1]: https://blog.rust-lang.org/releases/1.98.1/
[ref-2]: https://nnethercote.github.io/perf-book/profiling.html
[ref-3]: https://doc.rust-lang.org/cargo/reference/profiles.html
[ref-4]: https://doc.rust-lang.org/rustc/profile-guided-optimization.html
[ref-5]: ownership-and-concurrency.md
