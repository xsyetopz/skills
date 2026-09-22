# Kotlin performance

Identify Kotlin/JVM, Kotlin/Native, Kotlin/JS, or a multiplatform target before
applying advice. Record compiler/plugin versions, backend, build mode, and the
actual runtime. JVM allocation/JIT assumptions do not transfer to Native or JS.

Use the project's benchmark and profiler for the target. On JVM, account for JIT
warmup and use a proper harness such as JMH; on Native, compare optimized
binaries and investigate the selected memory manager. For multiplatform changes,
measure each claimed target rather than extrapolating from one.

On JVM hot paths, inspect boxing at nullable, generic, interface, and
value-class boundaries; value classes are not guaranteed to remain unboxed
everywhere. `inline` can remove certain call/closure costs but can increase code
size. Inspect generated code for the measured path instead of adding `inline` to
every helper.

Sequences trade intermediate collections for iterator/lambda overhead and lazy
evaluation. Measure the actual pipeline length and size, and preserve evaluation
order and side effects. A direct loop is appropriate when it yields a real
benefit without changing behavior.

For coroutines, preserve structured ownership, cancellation, dispatcher
semantics, and resource cleanup. A dispatcher switch has a cost, but eliminating
it can move blocking work onto the wrong thread. Do not catch and suppress
cancellation merely to keep a benchmark completing.

Sources: [Kotlin inline functions][kotlin-inline-functions], [Kotlin value
classes][kotlin-value-classes], [Kotlin coroutine
cancellation][kotlin-coroutine-cancellation], [Kotlin Native memory
management][kotlin-native-memory-management].

## Executable fixtures

Requires Kotlin/JVM compiler and JDK and POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in
[the kotlin assets](../assets/examples). Copy that directory intact when
adapting a fixture. Run only this language; the target project keeps its own
toolchain.

### Semantic regression cases

Source: [Semantics.kt][ref-semantics-kt].

| Case | Required contract |
| --- | --- |
| 1 | Eager side effects versus lazy short-circuiting |
| 2 | Materialization for repeated reads |
| 3 | Duplicate preservation |
| 4 | Immutable map-key snapshot |
| 5 | Unicode code points versus UTF-16 units |
| 6 | Checked integer arithmetic |
| 7 | Interrupt propagation |
| 8 | Atomic read-modify-write |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The
[shared contract](kotlin-backend-performance-executable-performance-fixtures.md)
explains input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Work in a copy of [the kotlin asset directory](../assets/examples). Run the
following commands relative to that copied directory.

Use JMH; do not turn the comparison CLI into a home-made timing library. The
bundled comparison programs test equivalence and expose callable functions, not
speedup claims. Run `sh verify.sh comparisons` from its root first.

Use the actual compiled Kotlin functions. Keep eager collection, Sequence and
Flow cases separate: they have different execution and suspension contracts.
Include boxing and materialization in the measured operation when consumers pay
those costs.

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

Source: [the isolated reproducer][ref-the-isolated-reproducer]. From the skill
root, run `sh assets/examples/verify.sh reproduction`. Direct commands below
assume a clean copy of the reproduction directory.

Expected: an expensive source is evaluated once and reused.

Actual: collecting the sequence twice evaluates it twice (`calls=4`).

Compile `Repro.kt` in a clean directory and run `ReproKt`. Exit zero means the
documented repeated evaluation was reproduced.

[kotlin-inline-functions]: https://kotlinlang.org/docs/inline-functions.html
[kotlin-value-classes]: https://kotlinlang.org/docs/inline-classes.html
[kotlin-coroutine-cancellation]:
  https://kotlinlang.org/docs/cancellation-and-timeouts.html
[kotlin-native-memory-management]:
  https://kotlinlang.org/docs/native-memory-manager.html
[source]: https://github.com/openjdk/jmh/tree/master/jmh-samples
[ref-the-fixture-execution-contract]:
  kotlin-backend-performance-executable-performance-fixtures.md
[ref-semantics-kt]: ../assets/examples/correctness/Semantics.kt
[ref-the-isolated-reproducer]: ../assets/examples/reproduction
