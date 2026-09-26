# Build configuration constructs

Cards for Cargo profile keys and rustc code-generation flags. Each
changes code across the whole crate graph, so each needs an
application-level measurement and a statement of its deployment
consequence. The profiles are declared in
[`constructs/Cargo.toml`](../assets/examples/constructs/Cargo.toml);
`sh assets/examples/verify.sh profiles` builds each, prints the binary
size, asserts the `panic = "abort"` binary is smaller than `release`,
and re-runs the oracle on it.

Release defaults per the [Cargo profiles reference][cargo-profiles]:
`opt-level = 3`, `debug = false`, `lto = false`, `codegen-units = 16`,
`panic = "unwind"`, `incremental = false`. Override a key for one build
with `CARGO_PROFILE_<NAME>_<KEY>` (for example
`CARGO_PROFILE_RELEASE_LTO=fat`).

Measured numbers (machine-specific: Apple M1 Max, rustc 1.98.1, LLVM
22.1.8) come from this loop in a copy of `assets/examples/constructs`
with `CARGO_TARGET_DIR` and `CARGO_BUILD_BUILD_DIR` set to `target`.
Build wall time covers `constructs` and `helper` only; std is
prebuilt.

```sh
for p in release release-cgu1 release-thin release-fat \
    release-abort release-size profiling; do
  /usr/bin/time -p cargo build -q --locked --profile "$p"
  wc -c < "target/$p/constructs"
  "target/$p/constructs" time inline-cross
done
```

| Profile | Binary bytes | Build wall s | inline baseline | inline candidate |
| --- | --- | --- | --- | --- |
| release | 680,368 | 1.78 | 4.612 µs | 2.703 µs |
| release-cgu1 | 632,800 | 2.98 | 4.605 µs | 2.692 µs |
| release-thin | 670,512 | 3.56 | 3.119 µs | 3.092 µs |
| release-fat | 577,280 | 6.95 | 3.108 µs | 3.110 µs |
| release-abort | 619,424 | 2.25 | 4.610 µs | 2.704 µs |
| release-size | 702,528 | 2.06 | 4.606 µs | 2.702 µs |
| profiling | 717,832 | 2.62 | 4.604 µs | 2.705 µs |

## Contents

- opt-level
- codegen-units = 1
- Thin LTO
- Fat LTO
- panic = "abort"
- Debug line tables for profiling
- target-cpu=native
- target_feature with runtime detection
- Profile-guided optimization

## opt-level

**Definition.** `opt-level` selects the LLVM optimization pipeline: `0`
none, `1` basic, `2` some, `3` all, `"s"` optimize for size, `"z"` size
and also no loop vectorization ([Cargo profiles][cargo-profiles]).

**Use when.**

- Measurements come from a dev build (`opt-level = 0`): switch to
  `--release` before measuring anything.
- Binary size is the objective: compare `"s"` and `"z"` against `3`,
  which remains the default.

**Do not use when.**

- `"s"`/`"z"` would be chosen without measuring: `release-size`
  (`"s"`) produced a larger binary (702,528 B) than `release`
  (680,368 B).
- A debug-profile timing would serve as evidence for production.

**Example.**

```toml
[profile.release-size]
inherits = "release"
opt-level = "s"
```

**Cost removed.** For `0 -> 3`: unoptimized code in every function.
For `"s"`/`"z"`: code size, possibly at runtime cost (the
[Performance Book][perf-book-build] says `"z"` "may also reduce runtime
speed").

**Verify.**

1. `sh assets/examples/verify.sh profiles` rebuilds and re-runs `verify`.
1. Compare the printed `PROFILE <name>: <bytes>` sizes and the
   application workload time under each profile.

## codegen-units = 1

**Definition.** `codegen-units` splits each crate into N units compiled
in parallel; the non-incremental default is 16. One unit gives LLVM the
whole crate at once, at the cost of compile time
([Cargo profiles][cargo-profiles]).

**Use when.**

- Release artifacts, where runtime or size matters more than compile
  time; the [Performance Book][perf-book-build] says a single unit can
  "improve runtime speed and reduce binary size".

**Do not use when.**

- Iterative development builds: build time rose 1.78 s -> 2.98 s for
  one small crate.

**Example.**

```toml
[profile.release-cgu1]
inherits = "release"
codegen-units = 1
```

**Cost removed.** Cross-unit call boundaries inside one crate.
Measured: binary 680,368 -> 632,800 B; the `inline-cross` timing did not
change (4.612 -> 4.605 µs) because that call crosses a crate, not a
unit.

**Verify.**

1. `sh assets/examples/verify.sh profiles` (oracle re-run on release).
1. Time the application workload under `release` and `release-cgu1`.

## Thin LTO

**Definition.** `lto = "thin"` performs link-time optimization across
all crates in the dependency graph, like fat LTO but taking
"substantially less time to run". The default, `lto = false`, is only
thin *local* LTO within one crate ([Cargo profiles][cargo-profiles]).

**Use when.**

- The profile shows hot, non-inlined calls into other crates
  (dependencies or your own workspace crates).

**Do not use when.**

- The hot path stays inside one crate.
- Link time is the bottleneck of the edit-compile loop.

**Example.**

```toml
[profile.release-thin]
inherits = "release"
lto = "thin"
```

**Cost removed.** Part of the cross-crate call overhead. Measured:
`helper::scale` (no `#[inline]`) baseline 4.612 -> 3.119 µs; build
1.78 -> 3.56 s. The `#[inline]` candidate under plain `release` stayed
faster (2.703 µs), and under thin LTO it slowed to 3.092 µs.

**Verify.**

1. `sh assets/examples/verify.sh profiles`.
1. Build with `--profile release-thin`, time the workload, and confirm
   in `--emit asm` (see the codegen reference) that the cross-crate call
   is gone.

## Fat LTO

**Definition.** `lto = true` or `"fat"` optimizes the whole crate graph as
one module ([Cargo profiles][cargo-profiles]). The
[Performance Book][perf-book-build] reports it can "improve runtime speed
by 10-20% or more, and also reduce binary size, at the cost of worse
compile times".

**Use when.**

- Final release artifacts. Combine it with `codegen-units = 1`.

**Do not use when.**

- The compile-time budget cannot absorb it: 1.78 -> 6.95 s for a tiny
  crate, and large graphs grow more.

**Example.**

```toml
[profile.release-fat]
inherits = "release"
lto = "fat"
codegen-units = 1
```

**Cost removed.** Measured: binary 680,368 -> 577,280 B; cross-crate
baseline 4.612 -> 3.108 µs.

**Verify.**

1. `sh assets/examples/verify.sh profiles`.
1. Application-level timing under `release` vs `release-fat`.

## panic = "abort"

**Definition.** `panic = "abort"` terminates the process on panic instead
of unwinding. Tests, benchmarks, build scripts, and proc macros ignore
the setting ([Cargo profiles][cargo-profiles]).

**Use when.**

- The binary never recovers from panics: no `catch_unwind`, no reliance
  on destructors running during a panic, no thread-panic isolation.
- Binary size matters; the [Performance Book][perf-book-build] says it
  "might reduce binary size and increase runtime speed slightly".

**Do not use when.**

- Any code calls `std::panic::catch_unwind`: it "only catches unwinding
  panics" ([docs][catch-unwind]). The oracle's `catch_unwind` check
  aborted the `release-abort` binary (exit 134) until it was gated on
  `cfg!(panic = "unwind")`.
- A server relies on a panicking worker thread being isolated: abort
  kills the whole process.
- Behavior is verified only by `cargo test`, which ignores the setting.

**Example.**

```toml
[profile.release-abort]
inherits = "release"
panic = "abort"
```

**Cost removed.** Unwind tables and landing pads. Measured: binary
680,368 -> 619,424 B; no timing change on `inline-cross`.

**Verify.**

1. `rg -n 'catch_unwind|panic::set_hook|JoinHandle::join' src/` and read
   each hit.
1. `sh assets/examples/verify.sh profiles` asserts the smaller size and
   re-runs `verify` on the abort binary (`cargo test` cannot).

## Debug line tables for profiling

**Definition.** `debug = "line-tables-only"` emits the minimum debug info
for file/line in backtraces and profilers, without variable info
([Cargo profiles][cargo-profiles]); the
[Performance Book][perf-book-profiling] recommends it for profiling
release builds, plus `-C force-frame-pointers=yes` for frame-pointer
unwinding.

**Use when.**

- A profiler shows only addresses or collapsed stacks for release code.

**Do not use when.**

- The shipped artifact would carry it by accident: use a separate
  `profiling` profile.

**Example.**

```toml
[profile.profiling]
inherits = "release"
debug = "line-tables-only"
```

```sh
RUSTFLAGS="-C force-frame-pointers=yes" \
  cargo build --profile profiling
```

**Cost removed.** Unattributed samples. Measured: samply resolved
function names from `target/profiling/constructs`; binary 717,832 B
versus 680,368 B; `inline-cross` timing unchanged (4.604 versus
4.612 µs).

**Verify.**

1. The profiling build passes the same oracle.
1. The profile shows source function names (see the samply card in the
   measurement reference).

## target-cpu=native

**Definition.** `-C target-cpu=native` generates code for the host CPU
and enables every feature it has; the binary "may not run on other
machines" ([codegen options][codegen]). List CPUs with
`rustc --print target-cpus`.

**Use when.**

- The binary runs only on the machine (or an identical fleet) it was
  built on, and `rustc --print cfg` shows extra `target_feature`
  values.

**Do not use when.**

- The artifact is distributed: use runtime detection instead (next
  card).
- The native CPU adds nothing: on this M1 Max,
  `rustc --print target-cpus` says native is `apple-m1`, and
  `diff <(rustc --print cfg) <(rustc --print cfg -C target-cpu=native)`
  printed nothing (28 `target_feature` lines both ways), so there is no
  effect to measure here.

**Example.**

```sh
diff <(rustc --print cfg) \
     <(rustc --print cfg -C target-cpu=native)
RUSTFLAGS="-C target-cpu=native" cargo build --release
```

**Cost removed.** Scalar or older-ISA code where the host has newer
instructions (the [Performance Book][perf-book-build]: "especially if the
compiler finds vectorization opportunities").

**Verify.**

1. The `diff` above lists the features gained; empty output means stop.
1. Time the workload with and without the flag on the deployment CPU.

## target_feature with runtime detection

**Definition.** `#[target_feature(enable = "...")]` compiles one function
with extra CPU features; calling it on a CPU without them is undefined
behavior ([Reference][ref-codegen]). Since Rust 1.86 such functions may
be safe, but callers without the feature still need `unsafe`
([1.86 release][rust-186]). `is_x86_feature_detected!` and
`is_aarch64_feature_detected!` check at runtime.

**Use when.**

- One distributed binary must use newer instructions where available.

**Do not use when.**

- The feature is already in the target baseline (for example NEON on
  `aarch64-apple-darwin`): there is nothing to dispatch.
- The check would run per element inside the hot loop: detect once,
  outside.

**Example.**

```rust
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
fn sum_u32_avx2(values: &[u32]) -> u32 {
    values.iter().fold(0u32, |sum, &v| sum.wrapping_add(v))
}

pub fn sum_u32_dispatch(values: &[u32]) -> u32 {
    #[cfg(target_arch = "x86_64")]
    if std::arch::is_x86_feature_detected!("avx2") {
        // PERF/SAFETY: the running CPU reported AVX2 just above.
        return unsafe { sum_u32_avx2(values) };
    }
    sum_u32_portable(values)
}
```

Runnable: `constructs/src/codegen.rs`. Tier: executed on aarch64 (the
portable path; oracle `target-feature`). The x86_64 branch was
type-checked with `cargo check --target x86_64-unknown-linux-gnu`
(rustc 1.98.0 from rustup) but not executed.

**Cost removed.** Scalar code on CPUs that have the wider instructions.
Not measured; measure on an x86_64 machine with AVX2.

**Verify.**

1. The oracle compares the dispatched result with the portable one.
1. On the target CPU, `--emit asm` shows `ymm` registers in
   `sum_u32_avx2`, and the workload time drops.

## Profile-guided optimization

**Definition.** PGO builds an instrumented binary with
`-Cprofile-generate=<abs dir>`, runs representative workloads, merges the
`.profraw` files with `llvm-profdata merge`, and rebuilds with
`-Cprofile-use=<file>.profdata` ([rustc PGO chapter][pgo]).
`llvm-profdata` must match rustc's LLVM version
(`rustup component add llvm-tools-preview`).

**Use when.**

- Build flags are settled and the workload is representative and
  stable; the [Performance Book][perf-book-build] says PGO "can improve
  runtime speed by 10% or more".

**Do not use when.**

- The training workload differs from production: the optimizer tunes
  the wrong paths.
- The available `llvm-profdata` comes from a different LLVM than
  rustc's.

**Example.**

```sh
RUSTFLAGS="-Cprofile-generate=/tmp/pgo-data" \
  cargo build --release --target=aarch64-apple-darwin
./target/aarch64-apple-darwin/release/constructs time
llvm-profdata merge -o /tmp/pgo-data/merged.profdata /tmp/pgo-data
RUSTFLAGS="-Cprofile-use=/tmp/pgo-data/merged.profdata" \
  cargo build --release --target=aarch64-apple-darwin
```

**Cost removed.** Poor layout and inlining decisions on hot paths.
Measure with the application workload.

**Verify.** Unexecuted: rustc was the Homebrew build (LLVM 22.1.8)
without the rustup `llvm-tools` component, and the only `llvm-profdata`
came from Apple's Command Line Tools, whose LLVM version was not
matched.

[cargo-profiles]: https://doc.rust-lang.org/cargo/reference/profiles.html
[perf-book-build]:
  https://nnethercote.github.io/perf-book/build-configuration.html
[perf-book-profiling]: https://nnethercote.github.io/perf-book/profiling.html
[catch-unwind]: https://doc.rust-lang.org/std/panic/fn.catch_unwind.html
[codegen]: https://doc.rust-lang.org/rustc/codegen-options/index.html
[ref-codegen]: https://doc.rust-lang.org/reference/attributes/codegen.html
[rust-186]: https://blog.rust-lang.org/2025/04/03/Rust-1.86.0/
[pgo]: https://doc.rust-lang.org/rustc/profile-guided-optimization.html
