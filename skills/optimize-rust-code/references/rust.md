# Profile and optimize Rust programming-language code

Record toolchain, target, Cargo profile, features, panic strategy, allocator,
LTO/codegen settings, and CPU target. Compare release artifacts with equivalent
supported targets. A debug-profile comparison says little about deployment
performance.

Use the existing benchmark framework and target profiler. Keep outputs
observable using the harness or a suitable black-box facility, and confirm the
optimizer has not eliminated the operation. Inspect generated code when a
claimed abstraction cost is important; iterators and generic dispatch can
optimize well, but “zero cost” is not a measurement of this path.

Investigate allocation, clones, ownership transfers, copies, data layout, cache
behavior, and contention based on the profile. `Clone` cost depends on the type;
a slice view can avoid a copy but changes lifetime and retention. Avoid
introducing shared ownership or interior mutability solely to work around a
design that should have a clear owner.

For `unsafe`, establish validity, alignment, bounds, initialization, aliasing,
provenance, and lifetime requirements for every affected API. An unsafe block is
a promise made by the code, not proof that the promise holds. Use Miri or
sanitizers where supported to find classes of defects, but do not claim their
success proves all executions safe.

Preserve async cancellation and drop behavior. Moving work across task
boundaries can change resource lifetime, `Send` requirements, and backpressure.
SIMD or CPU-specific instructions require supported dispatch/fallbacks when
distributing to heterogeneous machines.

Sources: [Cargo profiles][cargo-profiles], [Rust undefined
behavior][rust-undefined-behavior], [std::hint::black_box][std-hint-black-box],
[Miri](https://github.com/rust-lang/miri).

## Executable fixtures

Requires the checked-in Rust toolchain, Cargo, and its standard library and
POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in [the rust
assets](../assets/examples). Copy that directory intact when adapting a fixture.
Run only the selected language, not all toolchains.

### Semantic regression cases

Source: [semantics.rs][ref-semantics-rs].

| Case | Required contract |
| --- | --- |
| 1 | Checked integer overflow |
| 2 | Canonical output ordering |
| 3 | One-shot iterator reuse |
| 4 | Unicode scalar count versus bytes |
| 5 | Rc alias versus snapshot |
| 6 | Stable identity after compaction |
| 7 | Atomic read-modify-write |
| 8 | Errors must not become successful default values |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The [shared contract](executable-fixtures.md) explains
input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Work in a copy of [the rust asset directory](../assets/examples). Run the
following commands relative to that copied directory.

Use Criterion or the project's native benchmark target; do not turn the
comparison CLI into a home-made timing library. The bundled comparison programs
test equivalence and expose callable functions, not speedup claims. Run `sh
verify.sh comparisons` from its root first.

Keep optimization level, target features and dependency lock identical. Use
std::hint::black_box as appropriate, but inspect generated code rather than
claiming the barrier proves realistic work. Fixture generation and cloning
belong inside timing only when the operation includes them.

Integrate the selected baseline and candidate functions into the native
benchmark framework already used by the target repository. Record its exact
version and configuration; retain its result format, warmups/forks, parameters
and native controls. Test an independent expected result before measurement.
Keep one source of benchmark configuration instead of a separate skill_config
file. Declare any new package installation before performing it. Provision the
target benchmark dependencies explicitly; the example alone does not demonstrate
a performance gain.

Source: [source][source]

## Failure reproduction

Source: [the isolated reproducer](../assets/examples/reproduction). From the
skill root, run `sh assets/examples/verify.sh reproduction`. Direct commands
below assume a clean copy of the reproduction directory.

Expected: an eager replacement runs the callback three times.

Actual: constructing and dropping an iterator runs it zero times.

The verifier copies `repro.rs` into a temporary directory, compiles it, and runs
it. Exit zero means the documented timing difference was reproduced.

[cargo-profiles]: https://doc.rust-lang.org/cargo/reference/profiles.html
[rust-undefined-behavior]: https://doc.rust-lang.org/reference/behavior-considered-undefined.html
[std-hint-black-box]: https://doc.rust-lang.org/std/hint/fn.black_box.html
[source]: https://bheisler.github.io/criterion.rs/book/

[ref-the-fixture-execution-contract]: executable-fixtures.md
[ref-semantics-rs]: ../assets/examples/correctness/semantics.rs
