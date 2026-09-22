# Scala performance

Establish Scala version, JVM versus Scala.js/Native target, compiler flags,
library versions, and runtime. Do not apply JVM-specific explanations to every
backend. For JVM work, use a proper warmed/forked benchmark and
application-level profiling rather than timing a REPL expression.

Inspect collection construction, intermediate strict results, lazy views,
boxing, pattern matching, and closure allocation where the measured path spends
time. A view can reduce allocations but adds evaluation and traversal costs;
repeated consumption can repeat work. Preserve evaluation order, exceptions, and
single-use iterator behavior.

Choose primitive-friendly representation or specialization only for an evidenced
bottleneck. Generic types and value classes have context-dependent
representation; inspect generated code instead of declaring all wrappers
allocation-free. Replacing immutable structures with mutation requires an
explicit owner and equivalent visibility semantics.

For Futures or effect runtimes, identify the actual scheduler, blocking
boundaries, cancellation/resource semantics, and queue behavior. Increasing
parallelism can increase contention or memory pressure. Do not convert effectful
sequencing into eager execution merely to reduce wrapper counts.

Test tail recursion, stack behavior, empty and large inputs, and
equality/ordering contracts affected by representation changes. Report which
backend was measured and do not generalize a gain to untested targets.

Sources: [Scala collection views][scala-collection-views], [Scala
Futures][scala-futures], [sbt-jmh](https://github.com/sbt/sbt-jmh), [OpenJDK
JMH][ref-openjdk-jmh].

## Executable fixtures

Requires Scala CLI, Scala 3.3.8, and JDK 21 provisioned in advance and POSIX
`sh` for the convenience runner.

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
[the scala assets](../assets/examples). Copy that directory intact when adapting
a fixture. Run only this language; the target project keeps its own toolchain.

### Semantic regression cases

Source: [Semantics.scala][ref-semantics-scala].

| Case | Required contract |
| --- | --- |
| 1 | Eager effects versus lazy short-circuiting |
| 2 | One-shot iterator reuse |
| 3 | Mutable key versus immutable snapshot |
| 4 | Floating-point regrouping |
| 5 | Materializing side effects once |
| 6 | Checked integer overflow |
| 7 | Duplicate preservation |
| 8 | Atomic read-modify-write |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The
[shared contract](scala-backend-performance-executable-performance-fixtures.md)
explains input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Work in a copy of [the scala asset directory](../assets/examples). Run the
following commands relative to that copied directory.

Use JMH; do not turn the comparison CLI into a home-made timing library. The
bundled comparison programs test equivalence and expose callable functions, not
speedup claims. Run `sh verify.sh comparisons` from its root first.

Call the actual Scala implementation, retaining the collection type and compiler
settings. Check lazy view reuse, boxing, specialization and closure allocation.
Do not substitute a Java translation for the code under test.

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

Expected: a strict transformation invokes the callback for all three values.

Actual: a view consumed with `take(1)` invokes it once.

Run `scala-cli run Repro.scala --server=false` from a clean copy. Exit zero
means the documented timing difference was reproduced.

[scala-collection-views]:
  https://docs.scala-lang.org/overviews/collections-2.13/views.html
[scala-futures]: https://docs.scala-lang.org/overviews/core/futures.html
[source]: https://github.com/openjdk/jmh/tree/master/jmh-samples
[ref-openjdk-jmh]: https://openjdk.org/projects/code-tools/jmh/
[ref-the-fixture-execution-contract]:
  scala-backend-performance-executable-performance-fixtures.md
[ref-semantics-scala]: ../assets/examples/correctness/Semantics.scala
[ref-the-isolated-reproducer]: ../assets/examples/reproduction
