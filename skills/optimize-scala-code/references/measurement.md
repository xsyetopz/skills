# Measurement constructs

Each card attributes or proves a Scala/JVM cost. The runnable harness is
`assets/examples/`: `constructs/` (oracles), `bench/` (JMH), and
`verify.sh` (modes `verify`, `diagnostics`, `benchmark`, `measure`,
`profile`).

Tier: every mode of `verify.sh` was executed locally (`verify`,
`diagnostics`, `benchmark`, `measure`, `profile`, `sbt`). Measured
results in this skill are machine-specific: Apple M1 Max, macOS arm64,
OpenJDK 25.0.4.1 (Homebrew), scala-cli 1.16.0, Scala 3.8.4, JMH 1.37.
The machine was shared with other builds (load average above 30), so
timings are noisy; byte counts are deterministic for a given JDK, Scala
version, and input.

## Contents

- JMH through scala-cli
- JMH allocation profiler (-prof gc)
- sbt-jmh
- Allocation oracle with ThreadMXBean
- Bytecode inspection with javap
- JFR recording and jfr view
- Semantic oracle for collection rewrites

## JMH through scala-cli

**Definition.** Scala CLI's `--jmh` option compiles the inputs, runs the
JMH bytecode generator over `@Benchmark` classes, and starts the JMH runner;
`--jmh-version` selects JMH (default 1.37), and the directives
`//> using jmh` and `//> using jmhVersion` do the same in source
([CLI options][cli-jmh], [directives][cli-directives]). The option is
experimental and needs `--power`.

**Use when.**

- A method or small pipeline needs a baseline-versus-candidate timing on
  the JVM with warmup, forks, and dead-code protection.
- The project has no build tool, or needs a throwaway harness beside an
  sbt build.

**Do not use when.**

- The command passes `--server=false`: scala-cli 1.16.0 then warns
  that "`.java` files are not compiled to `.class` files", the
  JMH-generated sources are never compiled, and the runner fails. JMH
  needs the Bloop server.
- The claim is end-to-end latency: JMH isolates one operation; take the
  final number from the application's load test.
- The backend is Scala.js or Scala Native: JMH is JVM-only.

**Example.**

```scala
import java.util.concurrent.TimeUnit
import org.openjdk.jmh.annotations.*

@State(Scope.Benchmark)
@BenchmarkMode(Array(Mode.AverageTime))
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
class Pairs:
  var array: Array[Int] = Array.emptyIntArray
  @Setup def setup(): Unit = array = Array.tabulate(1000)(_ * 1000)
  @Benchmark def arrayMapSum: Int = array.map(_ + 1).sum
  @Benchmark def arrayWhile: Int =
    var sum = 0
    var i = 0
    while i < array.length do { sum += array(i) + 1; i += 1 }
    sum
```

```sh
mkdir -p tmp
scala-cli --power run --jmh constructs bench \
  --java-prop java.io.tmpdir="$PWD/tmp" -- -prof gc 'Pairs.array'
```

Runnable: `assets/examples/bench/Benchmarks.scala`, run by
`sh assets/examples/verify.sh measure` with `BENCH_FILTER`.

**Cost removed.** Wrong conclusions: JMH forks fresh JVMs, warms up
before measuring, and consumes returned values so the JIT cannot delete
the work ([JMH samples][jmh-samples]). Read `Score ± Error` in the result
table. Observed traps: `scala-cli run --jmh` without `--power` exits with
"The `--jmh` option is experimental", and a JMH run started while another
run held `$TMPDIR/jmh.lock` exited with "Another JMH instance
might be running"; a private `java.io.tmpdir` avoids it.

**Verify.**

1. Behavior: run the oracle first
   (`sh assets/examples/verify.sh verify`); JMH does not compare results.
1. Harness: `sh assets/examples/verify.sh benchmark` runs every benchmark
   once (`-f 1 -wi 0 -i 1 -r 100ms`) and prints `SMOKE PASSED`; that is
   not a timing result.
1. Benefit: `sh assets/examples/verify.sh measure` (2 forks, 5 warmup and
   5 measured 1 s iterations). Keep a change only if the candidate's
   `Score ± Error` interval does not overlap the baseline's.

## JMH allocation profiler (-prof gc)

**Definition.** JMH's `gc` profiler adds rows per benchmark:
`gc.alloc.rate` (MB/sec) and `gc.alloc.rate.norm` (bytes per operation),
plus `gc.count` and `gc.time` ([JMHSample_35_Profilers][jmh-profilers]).

**Use when.**

- The claim is an allocation change (boxing, intermediate collections,
  wrappers, closures).
- B/op must come from the same warmup and forking as the timing.

**Do not use when.**

- Reading `gc.alloc.rate` (MB/sec) as the allocation cost: it scales
  with speed. Compare `gc.alloc.rate.norm` only.
- Reading a tiny nonzero value (for example `0.002 B/op`) as a
  per-call allocation: it is JMH's own infrastructure amortized over
  many operations.

**Example.** Measured, bundled `Pairs` class, 2 forks, 5 iterations:

```sh
BENCH_FILTER='Pairs.array' sh assets/examples/verify.sh measure
```

```text
Benchmark                             Cnt      Score     Error  Units
Pairs.arrayMapSum:gc.alloc.rate.norm   10  35984.100 ±   0.065   B/op
Pairs.arrayWhile:gc.alloc.rate.norm    10      0.004 ±   0.002   B/op
```

**Cost removed.** None; it proves another card's allocation claim. The
candidate's `gc.alloc.rate.norm` should drop.

**Verify.**

1. `JMH_ARGS='-f 1' BENCH_FILTER='Pairs.array' sh
   assets/examples/verify.sh measure`, then read the
   `:gc.alloc.rate.norm` rows in `bench-results/jmh.txt`.
1. Cross-check with the ThreadMXBean oracle below; the two should agree
   in order of magnitude.

## sbt-jmh

**Definition.** sbt-jmh is an sbt AutoPlugin: add
`addSbtPlugin("pl.project13.scala" % "sbt-jmh" % "0.4.8")` to
`project/plugins.sbt`, `enablePlugins(JmhPlugin)` to the benchmark
project, and run `Jmh/run <JMH options> <regex>`. Version 0.4.8 lists
sbt 1.3.0/2.0 support and JMH 1.37 ([sbt-jmh README][sbt-jmh]).

**Use when.**

- The code under test lives in an sbt build and the benchmark must use
  the build's dependencies and `scalacOptions`.

**Do not use when.**

- Benchmarks would go in the production module: the README advises a
  separate project because JMH generates code.
- Results would come from `Jmh/run -i 1 -wi 1 -f1`: the README
  recommends 10 to 20 warmup and measurement iterations and forking.
- `JAVA_TOOL_OPTIONS=-Djava.io.tmpdir=...` is set for sbt 2: the thin
  client then printed "failed to connect to server", and
  `sbt --server` with it exited 133. Pass JVM options to the forked JMH
  runner through `Jmh / run / javaOptions` instead.

**Example.**

```scala
// project/plugins.sbt
addSbtPlugin("pl.project13.scala" % "sbt-jmh" % "0.4.8")
// build.sbt
scalaVersion := "3.8.4"
enablePlugins(JmhPlugin)
// JMH takes a lock file in java.io.tmpdir; JMH_TMPDIR gives each run its
// own directory on a shared machine.
Jmh / run / javaOptions ++=
  sys.env.get("JMH_TMPDIR").map(d => s"-Djava.io.tmpdir=$d").toSeq
```

```sh
sbt -batch 'Jmh/run -i 10 -wi 10 -f 2 -prof gc .*Pairs.*'
sbt shutdown
```

Runnable: `assets/examples/sbt/` (sbt 2.0.9, compiles `../constructs`
and `../bench`), run by `sh assets/examples/verify.sh sbt`.

**Cost removed.** Same as the scala-cli harness, inside sbt. The sbt 2
thin client starts a background server ("starting sbt
server in the background"); without `sbt shutdown`, a JVM keeps running
after the command.

**Verify.**

1. `sh assets/examples/verify.sh sbt` (tier: executed locally with sbt
   2.0.9 and JDK 25) prints one row per benchmark and `SMOKE PASSED`.
1. Read `gc.alloc.rate.norm` and `Score ± Error` from a full run as
   above.

## Allocation oracle with ThreadMXBean

**Definition.**
`com.sun.management.ThreadMXBean.getCurrentThreadAllocatedBytes()`
(since JDK 14 per the javadoc) approximates the heap bytes the current
thread has allocated ([javadoc][threadmxbean]). The delta around N calls,
divided by N, is bytes per operation.

**Use when.**

- A test must fail when a candidate starts allocating again (a
  regression assertion that runs in seconds, unlike JMH).
- B/op must be exact and use the equivalence oracle's inputs.

**Do not use when.**

- The measured calls have not warmed up: interpreted and C1 code
  allocates where C2 code does not (escape analysis). Run thousands of
  calls first.
- The operation is passed as `() => Long`: a Scala 3 lambda of type
  `() => Long` that calls a method boxed its result (24 B/op), while
  `() => 42L` measured 0. Pass a non-generic SAM (`LongOp` in `Check.scala`) for
  primitive results.
- Work runs on other threads (futures, parallel collections): the
  counter is per thread.

**Example.**

```scala
trait LongOp:
  def run(): Long

private val threads = ManagementFactory.getThreadMXBean
  .asInstanceOf[com.sun.management.ThreadMXBean]

def bytesPerOpLong(op: LongOp, warm: Int = 20000, reps: Int = 2000)
    : Double =
  var i = 0
  while i < warm do { sinkLong = op.run(); i += 1 }
  val before = threads.getCurrentThreadAllocatedBytes()
  i = 0
  while i < reps do { sinkLong = op.run(); i += 1 }
  (threads.getCurrentThreadAllocatedBytes() - before).toDouble / reps
```

Runnable: `assets/examples/constructs/Check.scala`; the self-test asserts
a no-op measures below 1 B/op.

**Cost removed.** Regressions that timing noise hides. Assert ratios
(`candidate <= baseline * r`) or `< 1 B/op`, not exact byte counts,
because object header sizes change with JVM flags.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints
   `PASS harness self-test (no-op 0.00 B/op)` before any construct.
1. Each `PASS <name> allocation (baseline X B/op, candidate Y B/op)` line
   is the claim; a `FAIL` exits 1.

## Bytecode inspection with javap

**Definition.** `javap -c -p` disassembles every method of a class,
including private ones; `-s` prints internal type descriptors
([javap manual][javap]). It shows Scala's encodings: boxing calls, lambda
factories, `tableswitch`, lazy-val fields.

**Use when.**

- A card's mechanism is a compile-time transformation: opaque types,
  value classes, `inline`, `@tailrec`, `@switch`, lazy vals, extension
  methods, string interpolators, `Function1` specialization.
- The compiler's output must be checked against your assumption before
  measuring.

**Do not use when.**

- The claim is a runtime cost: C2 may remove a `new` that javap shows
  (escape analysis). Pair javap with the allocation oracle.
- Array types are read from the default output: Scala 3.8.4 wrote a
  Java generic signature of `double[]` for a method returning
  `Array[MetersVC]`, while the descriptor from `javap -s` is
  `[Lconstructs/MetersVC;`. Assert on `descriptor:` lines.

**Example.**

```sh
scala-cli compile constructs --server=false -d classes
javap -c -p -cp classes 'constructs.Switch$' | grep switch
javap -s -p -cp classes 'constructs.Units$' | grep -A1 opaqueArray
```

```text
         3: tableswitch   { // 0 to 3
  public double[] opaqueArray(int);
    descriptor: (I)[D
```

**Cost removed.** Wrong mechanism assumptions (a `@switch` that compiled
to `if` chains, a lazy val read that is a volatile load plus `instanceof`).

**Verify.**

1. `sh assets/examples/verify.sh diagnostics` runs every bytecode
   assertion and prints `ALL DIAGNOSTICS PASSED`.

## JFR recording and jfr view

**Definition.** JDK Flight Recorder records CPU samples and allocation
samples with low overhead when started with
`-XX:StartFlightRecording=filename=<f>.jfr`; `jfr view <view> <file>`
prints aggregated tables such as `hot-methods` and
`allocation-by-class` ([jfr manual][jfr]).

**Use when.**

- It is not yet known which method or type dominates CPU or allocation
  in the real application.
- Production-like runs cannot load a profiler agent (JFR ships in the
  JDK).

**Do not use when.**

- Allocation samples would be read as exact counts: they are sampled.
  Take B/op from JMH `-prof gc` or the ThreadMXBean oracle.
- The backend is Scala.js or Scala Native: JFR is JVM-only.

**Example.**

```sh
scala-cli run constructs --server=false --main-class constructs.profile \
  --java-opt -XX:StartFlightRecording=filename=profile.jfr -- 5
jfr view hot-methods profile.jfr | head -n 20
jfr view allocation-by-class profile.jfr | head -n 20
```

**Cost removed.** Optimizing the wrong code. Measured on the bundled
loop (an immutable `Map` rebuilt per batch): `allocation-by-class` put
`java.lang.Object[]` (75.57%) and
`scala.collection.immutable.BitmapIndexedMapNode` (20.63%) on top, and
`hot-methods` listed `BitmapIndexedMapNode.getOrElse` and `.updated`;
the fix is the mutable map card in the collections reference.

**Verify.**

1. `sh assets/examples/verify.sh profile` writes
   `bench-results/profile.jfr` and prints both views.
1. After a change, record again with the same workload; the attributed
   rows must shrink.

## Semantic oracle for collection rewrites

**Definition.** A baseline-versus-candidate check on the same inputs
that also pins the collection semantics a rewrite can silently change:
laziness, single traversal of iterators, duplicate handling, overflow,
and floating-point grouping.

**Use when.**

- A change alters a collection type, strictness, or evaluation
  order.

**Do not use when.**

- The test covers only the happy path: add empty input, boundary
  values (`Int.MaxValue`), duplicates, and side-effect counts.

**Example.** Traps the bundled oracle asserts:

```scala
var calls = 0
val v = Vector(1, 2, 3).view.map { x => calls += 1; x }
v.toList; v.toList
assert(calls == 6)                 // a view recomputes on every traversal
val once = Iterator(1, 2, 3)
once.toList
assert(once.toList == Nil)         // an iterator is consumed once
assert(List(2, 1, 2).toSet.toList == List(2, 1)) // duplicates dropped
val (a, b, c) = (1e16, -1e16, 1.0)
assert((a + b) + c != a + (b + c)) // regrouping changes Double sums
```

Runnable: `CollectionChecks` in `assets/examples/constructs/`.

**Cost removed.** Wrong "optimizations" that pass a happy-path test.

**Verify.**

1. `sh assets/examples/verify.sh verify` prints `PASS view-reevaluates`,
   `PASS iterator is one-shot`, `PASS toSet drops duplicates`, and
   `PASS double addition is not associative`.

[cli-jmh]: https://scala-cli.virtuslab.org/docs/reference/cli-options#--jmh
[cli-directives]: https://scala-cli.virtuslab.org/docs/reference/directives#benchmarking-options
[jmh-samples]: https://github.com/openjdk/jmh/tree/master/jmh-samples/src/main/java/org/openjdk/jmh/samples
[jmh-profilers]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java
[sbt-jmh]: https://github.com/sbt/sbt-jmh
[threadmxbean]: https://docs.oracle.com/en/java/javase/25/docs/api/jdk.management/com/sun/management/ThreadMXBean.html#getCurrentThreadAllocatedBytes()
[javap]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/javap.html
[jfr]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/jfr.html
