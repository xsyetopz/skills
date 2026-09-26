---
name: optimize-rust-code
description: >-
  Profiles and optimizes Rust CPU time, allocations, and I/O with Criterion,
  samply, allocation counts, and assembly. Use when a Rust benchmark or
  profile shows the cost. Not for unmeasured unsafe rewrites.
---

# Optimize Rust Code

Make a measured Rust hot path cheaper without changing observable behavior.
Each change applies one reference card to a cost that a profile attributes,
is proven equivalent by an oracle, and is kept only if the metric the card
names improves: allocation calls, inner I/O calls, hash computations, an
instruction pattern in the assembly, or a Criterion interval. The cards
state when a construct is wrong and what it breaks, so read the card before
applying a construct.

## Workflow

1. Record the target: `rustc -Vv`, `cargo -V`, the `[profile.*]` tables
   in `Cargo.toml`, `.cargo/config.toml` (`rustflags`, `build-dir`),
   `RUSTFLAGS`, features, and `rust-version`. Keep the toolchain and
   profile unless the task is the build configuration itself.
1. Reproduce the workload with `cargo build --release` (never a dev
   build). Pick the metric the user cares about: time per operation,
   end-to-end wall time, allocations, peak memory, or binary size.
1. Attribute the cost before editing:
   - CPU: build with the `profiling` profile and run `samply record`
     ([measurement](references/measurement.md#samply)); `perf` does not
     exist on macOS.
   - Allocations: the counting global allocator
     ([measurement](references/measurement.md#counting-global-allocator)).
   - One function: a Criterion benchmark with `black_box` inputs.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty, one element, boundary lengths, non-ASCII text, and
   error or panic paths. The bundled `constructs verify` shows the shape.
1. Apply the change. Put a `// PERF/SAFETY:` comment on every `unsafe`
   block, `get_unchecked`, and `#[target_feature]` call stating the proof.
1. Verify with the card's **Verify** steps: behavior first, then the
   named metric. Assembly claims use `cargo rustc --release --lib --
   --emit asm -C codegen-units=1` on a `#[unsafe(no_mangle)]` symbol.
1. Measure baseline and candidate with the same toolchain, profile, flags,
   input, and machine (Criterion `--save-baseline`/`--baseline`, or
   hyperfine for whole processes). Keep the change only if the interval
   separates and the application workload also improves.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| `Vec` growth reallocations (`realloc` in counts) | [with_capacity](references/allocation.md#vecwith_capacity), [reserve](references/allocation.md#reserve-before-extend_from_slice) |
| New `Vec`/`String` per loop iteration | [clear reuse](references/allocation.md#reuse-a-buffer-with-clear), [read_line](references/collections-io.md#read_line-into-a-reused-string) |
| `.clone()`/`to_string()` only to call a function | [borrowed params](references/allocation.md#borrowed-parameters-instead-of-owned-ones) |
| `x = y.clone()` into a long-lived value | [clone_from](references/allocation.md#clone_from-into-an-existing-value) |
| Function returns `String` but usually returns input unchanged | [Cow](references/allocation.md#cow-for-conditional-modification) |
| `format!` in a loop, `s = s + ...` | [write!](references/allocation.md#write-into-a-string-instead-of-per-item-format), [push_str](references/allocation.md#push_str-into-a-presized-string) |
| Small fixed-bound scratch `Vec` | [stack array](references/allocation.md#fixed-size-stack-array-instead-of-a-scratch-vec) |
| Atomic refcount traffic (`Arc::clone` in hot calls) | [borrow](references/allocation.md#borrow-instead-of-cloning-an-arc), [Rc](references/allocation.md#rc-instead-of-arc-for-single-threaded-sharing) |
| `panic_bounds_check` in a hot loop | [iterators](references/codegen.md#iterators-instead-of-indexing), [reslice](references/codegen.md#reslice-before-the-loop), [chunks_exact](references/codegen.md#chunks_exact), [get_unchecked](references/codegen.md#get_unchecked-behind-a-checked-invariant) |
| Scalar float reduction in a hot loop | [accumulators](references/codegen.md#independent-accumulators-for-float-auto-vectorization), [std::simd](references/codegen.md#stdsimd-nightly-only) |
| `Vec<Box<dyn Trait>>`, `blr`/indirect calls | [generics](references/codegen.md#generics-instead-of-box-dyn-trait), [enum dispatch](references/codegen.md#enum-dispatch-for-a-closed-set-of-types) |
| Small cross-crate function not inlined | [#\[inline\]](references/codegen.md#inline-across-crates), [LTO](references/build-profiles.md#thin-lto) |
| Stable `sort` on primitives | [sort_unstable](references/codegen.md#sort_unstable) |
| Hand-written delimiter or byte search | [str search](references/codegen.md#memchr-backed-str-search), [slice contains](references/codegen.md#slice-contains-for-bytes) |
| `contains_key` then `insert`/`get_mut` | [entry](references/collections-io.md#hashmap-entry-api) |
| HashMap resizes; SipHash hot on trusted keys | [with_capacity](references/collections-io.md#hashmapwith_capacity), [FxHashMap](references/collections-io.md#fxhashmap-for-trusted-keys) |
| Many small `write`/`read` calls on files or sockets | [BufWriter](references/collections-io.md#bufwriter-around-many-small-writes), [BufReader](references/collections-io.md#bufreader-around-many-small-reads) |
| `println!` in a loop dominates | [lock](references/collections-io.md#lock-stdout-once), [buffered stdout](references/collections-io.md#buffered-stdout) |
| Independent CPU-heavy items, idle cores | [rayon](references/collections-io.md#rayon-parallel-iterators) |
| Release profile untouched, whole-program speed or size | [codegen-units](references/build-profiles.md#codegen-units--1), [fat LTO](references/build-profiles.md#fat-lto), [panic abort](references/build-profiles.md#panic--abort), [opt-level](references/build-profiles.md#opt-level), [PGO](references/build-profiles.md#profile-guided-optimization) |
| Newer CPU instructions available | [target-cpu](references/build-profiles.md#target-cpunative), [target_feature](references/build-profiles.md#target_feature-with-runtime-detection) |
| Profiler shows addresses, no names | [line tables](references/build-profiles.md#debug-line-tables-for-profiling) |

## Rules

- Measure release builds only. Dev builds (`opt-level = 0`) also turn on
  `overflow-checks`, so they differ in behavior as well as speed.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric does not move; the iterators card's own
  run removed a bounds check without changing the time.
- A candidate that does less work is invalid: skipped validation, a
  truncating `zip` instead of a panicking index, a cached result, a
  smaller input, or an error turned into a default value
  (`unwrap_or_default()` on a parse).
- Preserve semantics the rewrite can silently change: byte offsets vs
  char counts in `str`, stable vs unstable sort order for ties, float
  rounding order (and `-0.0` from an empty `Sum`), lazy iterator side
  effects, one-shot iterators, hash-map iteration order, and whether an
  `Rc`/`Arc` handle aliases a value that a deep clone used to snapshot.
- `unsafe` for speed needs: the assembly proving the safe form still has
  the check, a proof in a `// PERF/SAFETY:` comment, and the oracle.
  Miri needs nightly; say so if it was not run.
- Build-profile and `RUSTFLAGS` changes affect every crate and the
  deployment target. State the consequence (`panic = "abort"` disables
  `catch_unwind`; `target-cpu=native` binaries may not run elsewhere) and
  measure the application, not a microbenchmark.
- Allocation assertions compare baseline and candidate counts measured in
  the same run; the optimizer may elide allocations, so never assert an
  exact baseline count.
- Only numbers you measured (state machine and toolchain) or numbers from
  a linked primary source go in the report.

## Bundled tools

`assets/examples/verify.sh` copies the catalog to a temporary directory and
builds there (it also redirects `CARGO_BUILD_BUILD_DIR`):

- `verify` (default): equivalence, allocation, and call-count checks for
  every pair, plus stdout output comparison.
- `benchmark`: runs every pair once; smoke only, no timing.
- `asm`: emits assembly and asserts bounds checks, calls, atomics, and
  vector instructions per function (SIMD, `blr`, and atomics on aarch64).
- `time [filter]`: std-only `Instant` harness plus hyperfine.
- `profiles`: builds every `[profile.*]` card and prints binary sizes.
- `ecosystem` and `measure`: rayon and rustc-hash oracles, and Criterion
  benchmarks (`BENCH_FILTER`, `BENCH_OUT`); both fetch crates.io
  dependencies pinned by `ecosystem/Cargo.lock`.

`assets/examples/nightly/simd.rs` needs a nightly toolchain and is not
built by the script.

## References

- [Measurement](references/measurement.md): `black_box`, std harness,
  Criterion, baselines, hyperfine, counting allocator and wrappers,
  `--emit asm`, samply, flamegraph, Instruments.
- [Build profiles](references/build-profiles.md): opt-level,
  codegen-units, thin and fat LTO, panic abort, line tables, target-cpu,
  target_feature, PGO.
- [Allocation](references/allocation.md): capacity, buffer reuse,
  borrowed parameters, clone_from, Cow, strings, stack arrays, Arc, Rc.
- [Code generation](references/codegen.md): bounds checks,
  vectorization, SIMD, dispatch, inlining, sorting, search.
- [Collections and I/O](references/collections-io.md): entry API, map
  capacity, FxHashMap, buffered I/O, stdout, rayon.

## Completion evidence

The final report contains:

- `rustc -Vv`, profile settings, `RUSTFLAGS`, OS and CPU;
- the profile or allocation count that attributed the cost;
- the card applied and its preconditions checked;
- the oracle command and result, including edge and panic cases;
- baseline and candidate numbers from the same machine and build, with
  units and interval or ± range, plus the application-level result;
- every check not run (Miri, nightly, other architectures, Xcode-only
  profilers) stated as not verified.
