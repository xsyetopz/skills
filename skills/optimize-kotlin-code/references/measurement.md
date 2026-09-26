# Measurement constructs

How to attribute and prove a Kotlin/JVM cost: bytecode, allocation
counters, escape-analysis control runs, JMH, virtual time, and JFR. Every
command runs against the catalog in `assets/examples/constructs/` through
`assets/examples/verify.sh`, which builds in a temporary copy.

Local results in all references are machine-specific: Apple M1 Max, macOS
arm64, OpenJDK 25.0.4.1 (Homebrew), Kotlin 2.4.20 with `jvmTarget` 17,
kotlinx.coroutines 1.11.0, JMH 1.37, Maven 3.9.16. Other agents shared
the machine during measurement. Byte counts are deterministic for a given
JDK, flags, and input; timings are not portable.

Tier: Executed for every card except kotlinx-benchmark and the
Native/JS boundary, which are Not runnable here (stated in the cards).

## Contents

- javap bytecode inspection
- Thread allocation counter
- Escape-analysis control run
- JMH through Maven for Kotlin
- JMH gc profiler
- Virtual time with runTest
- JFR allocation profile
- kotlinx-benchmark (Gradle)
- Kotlin/Native and Kotlin/JS boundary

## javap bytecode inspection

**Definition.** `javap -c -p` disassembles compiled `.class` files into
JVM bytecode ([javap manual][javap]). Kotlin top-level functions in
`File.kt` land in class `FileKt`. Inline functions, lambdas, boxing,
range lowering, and `when` lowering each show up as specific
instructions.

**Use when.**

- A card claims a compile-time transformation: no `Function1` object, no
  `Integer.valueOf`, no `kotlin/ranges` call, `tableswitch` vs
  `instanceof` chain.
- You must know what the project's Kotlin compiler version emits before
  trusting a folk rule. Several changed across Kotlin 2.x, such as
  `invokedynamic` lambdas by default since 2.0 ([What's new in
  2.0][whatsnew20]).

**Do not use when.**

- You want to prove a runtime cost. Bytecode shows what the JIT starts
  from; C2 inlining and escape analysis can erase an allocation that the
  bytecode contains (see the escape-analysis card). Pair it with an
  allocation counter or JMH.

**Example.**

```sh
javap -c -p -cp target/classes constructs.InlineKt \
  | awk '/ countAboveBaseline\(/,/^$/'
```

Excerpt of the output (owner names shortened to fit 80 columns):

```text
public static final int countAboveBaseline(int[], int);
  3: iload_1
  4: invokedynamic #0:invoke:(I)Lkotlin/jvm/functions/Function1;
  9: invokestatic  countIfBaseline:([ILkotlin/jvm/functions/Function1;)I
```

Runnable: the `expect` helper in `assets/examples/verify.sh` extracts one
method body and counts lines that match a regex (`some`, `none`, or an
exact count).

**Cost removed.** Ambiguity: the assertion states which instruction is
present before and absent after. It measures neither time nor bytes.

**Verify.**

1. `sh assets/examples/verify.sh bytecode` prints one `BYTECODE` line per
   assertion and ends with `BYTECODE PASSED`.
1. In a target project, run the same `javap` on the built class of the
   changed function and compare baseline and candidate bodies.

## Thread allocation counter

**Definition.**
`com.sun.management.ThreadMXBean.getCurrentThreadAllocatedBytes()` (since
JDK 14) returns "an approximation of the total amount of memory, in
bytes, allocated in heap memory for the current thread"
([ThreadMXBean][threadmx]). The delta around N calls, divided by N, is
bytes per call.

**Use when.**

- An oracle in an ordinary `main` or unit test must assert that a
  candidate allocates less than a baseline, or nothing.

**Do not use when.**

- The code has not reached C2: the interpreter and C1 allocate objects
  that C2 removes. Warm up first and run with `-Xbatch`, which makes
  compilation a foreground task ([java manual][javaman]).
- The measured lambda returns a primitive through `Any?`: the counter
  includes the boxing of the result. The catalog measures that boxing
  alone and subtracts it (`Harness.boxOverhead`).
- The work runs on other threads (coroutines on `Dispatchers.Default`):
  the counter only sees the calling thread.

**Example.**

```kotlin
private val threads =
    ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean

fun bytesPerCall(warm: Int, runs: Int, body: () -> Any?): Long {
    repeat(warm) { sink = body() }
    val before = threads.currentThreadAllocatedBytes
    repeat(runs) { sink = body() }
    return (threads.currentThreadAllocatedBytes - before) / runs
}
```

Runnable: `Harness.kt`. `sink` is a `@Volatile` field so results escape.

**Cost removed.** Not an optimization; it makes allocation claims
checkable. Output lines look like
`PASS alloc buildList: baseline 4075568 B/call, candidate 19632 B/call`.

**Verify.**

1. `sh assets/examples/verify.sh verify` ends with `ALL CHECKS PASSED`.
1. Rerun it: byte counts repeat exactly on the same JDK and flags.

## Escape-analysis control run

**Definition.** C2 escape analysis replaces non-escaping objects with
scalars. `-XX:-DoEscapeAnalysis` turns it off ([java manual][javaman]),
exposing allocations that the bytecode contains but the default JIT
removes.

**Use when.**

- A bytecode assertion shows an allocation (lambda, `Ref.IntRef`,
  `IntRange`, `Pair`) but the allocation counter shows no difference.
  The control run tells you whether the cost is latent and will return
  when the callee stops being inlined (large body, megamorphic call
  site).

**Do not use when.**

- You want production numbers. Escape analysis is on by default; the
  control run is diagnostic only.

**Example.**

```sh
sh assets/examples/verify.sh noea
```

**Cost removed.** None by itself. Measured (machine-specific): the
non-inline `countIf` baseline allocates 0 B/call with escape analysis and
13,968 B/call without it; the inline candidate allocates 0 B in both. The
captured-`var` baseline: 0 B vs 13,984 B. `associateWith` vs `associate`:
equal (48,272 B) with escape analysis; 48,304 B vs 72,304 B without.

**Verify.**

1. `sh assets/examples/verify.sh noea` prints `INFO alloc` lines only;
   equality checks still run and must pass.
1. Compare each `INFO` line with the same line from `verify`.

## JMH through Maven for Kotlin

**Definition.** JMH generates its harness from annotated classes. For
Kotlin, the JMH `jmh-kotlin-benchmark-archetype` 1.37 compiles Kotlin
first, runs `JmhBytecodeGenerator` on the classes, compiles the generated
Java, and shades one jar whose main class is `org.openjdk.jmh.Main`
([JMH repository][jmh]).

**Use when.**

- Time per operation or throughput decides the change, and the project
  builds with Maven. Gradle projects use kotlinx-benchmark or the JMH
  Gradle plugin.

**Do not use when.**

- The benchmark class is `final`: JMH subclasses `@State` classes, and
  Kotlin classes are final by default. Declare them `open`, or use the
  `allopen` compiler plugin as kotlinx-benchmark does.
- You would keep the archetype's pinned plugin versions: it pins Java
  target 1.8 and old plugins. The catalog `pom.xml` uses
  kotlin-maven-plugin 2.4.20 (`jvmTarget` 17), exec-maven-plugin 3.6.2,
  maven-compiler-plugin 3.15.0 (`release` 17, `proc` none), and
  maven-shade-plugin 3.6.2.

**Example.**

```kotlin
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(1)
open class Pairs {
    private val list = List(10_000) { it - 5_000 }

    @Benchmark fun takeBaseline() = firstSquaresBaseline(list, 10)
    @Benchmark fun takeCandidate() = firstSquaresCandidate(list, 10)
}
```

Runnable: `Benchmarks.kt` and `pom.xml` under
`assets/examples/constructs/`. Returning the result lets JMH consume it,
which prevents dead-code elimination.

**Cost removed.** None by itself; it produces `Score ± Error` per
benchmark. Build output: one `target/constructs.jar`.

**Verify.**

1. `sh assets/examples/verify.sh benchmark` runs every benchmark once and
   prints `SMOKE PASSED` (not a timing result).
1. `BENCH_FILTER=take sh assets/examples/verify.sh measure`. JMH refuses
   to start while another JMH run holds its lock file. Wait, or set
   `JMH_IGNORE_LOCK=1` and record that the numbers are contaminated.

## JMH gc profiler

**Definition.** `-prof gc` adds `gc.alloc.rate.norm`, the bytes allocated
per benchmark operation, to each JMH result ([JMHSample_35][jmh35]).

**Use when.**

- The claim is "fewer bytes per operation", and you need it next to the
  time score from the same run.

**Do not use when.**

- The benchmark allocates in setup that runs per invocation
  (`Level.Invocation`): the profiler does not separate setup allocation.

**Example.**

```sh
java -jar target/constructs.jar -prof gc -rf json \
  -rff out/jmh-result.json 'Pairs.take'
```

**Cost removed.** None by itself. Read `·gc.alloc.rate.norm` in `B/op`;
the byte numbers in the other references come from this column.

**Verify.**

1. `BENCH_OUT=/tmp/jmh BENCH_FILTER=take sh assets/examples/verify.sh
   measure`, then check that `/tmp/jmh/jmh-result.json` has a
   `secondaryMetrics` entry `gc.alloc.rate.norm` for each benchmark.
   Without `BENCH_OUT`, the JSON is deleted with the temporary copy.
1. The candidate's `B/op` is lower than the baseline's in the same run.

## Virtual time with runTest

**Definition.** `runTest` from kotlinx-coroutines-test runs coroutines on
a `TestCoroutineScheduler` that skips `delay` by advancing virtual time.
`testScheduler.currentTime` reads it ([kotlinx-coroutines-test][cotest]).

**Use when.**

- A coroutine card claims less waiting (concurrent `async`, `buffer`,
  `conflate`, channel capacity): virtual time turns the claim into an
  exact number with no wall-clock noise.

**Do not use when.**

- The code switches to `Dispatchers.Default` or `Dispatchers.IO`:
  "Delays are only skipped in the test dispatcher". Inject a dispatcher.
- The claim is about CPU time or thread blocking: virtual time counts
  only `delay`.

**Example.**

```kotlin
var elapsed = 0L
runTest {
    pricesConcurrent(listOf(1, 2, 3)) // three delay(100) calls
    elapsed = testScheduler.currentTime
}
check(elapsed == 100L) // 300L for the sequential version
```

`testScheduler.currentTime` is `@ExperimentalCoroutinesApi` in 1.11.0.
Without `@OptIn`, kotlinc reports an opt-in warning, which the catalog's
`-Werror` build turns into a failure (observed locally).

**Cost removed.** Wall-clock noise in coroutine timing claims.

**Verify.**

1. `sh assets/examples/verify.sh verify coroutines` prints
   `PASS async virtual time concurrent` and the flow and channel lines.

## JFR allocation profile

**Definition.** JDK Flight Recorder samples allocations and CPU in a
running JVM. `-XX:StartFlightRecording=filename=...,settings=profile`
starts it ([java manual][javaman]), and `jfr view allocation-by-class`
aggregates the recording ([jfr manual][jfrman]; `jfr --help view` lists
the views).

**Use when.**

- You do not yet know which types dominate allocation in the real
  workload. Run it before choosing a card.

**Do not use when.**

- You need exact per-call bytes: JFR samples. After attribution, use the
  thread counter or JMH `-prof gc`.

**Example.**

```sh
java -XX:StartFlightRecording=filename=app.jfr,settings=profile \
  -jar app.jar
jfr view allocation-by-class app.jfr
jfr view cpu-time-hot-methods app.jfr
```

**Cost removed.** Guesswork about the allocation source.

**Verify.**

1. `sh assets/examples/verify.sh jfr` records the collection oracles and
   prints the allocation-by-class table.

## kotlinx-benchmark (Gradle)

**Definition.** kotlinx-benchmark is a Gradle plugin
(`org.jetbrains.kotlinx.benchmark`, 0.5.0 at the time of writing) that
runs the same benchmark sources on Kotlin/JVM (through JMH), Kotlin/JS,
Kotlin/Native, and Kotlin/Wasm. The `benchmark` task runs all targets,
and `<target>Benchmark` runs one ([kotlinx-benchmark][kxbench]).

**Use when.**

- The project already builds with Gradle, or it is multiplatform and
  each target needs its own number.

**Do not use when.**

- The project is Maven-only: use the JMH card instead.

**Example.**

```kotlin
plugins {
    kotlin("jvm") version "2.4.20"
    kotlin("plugin.allopen") version "2.4.20"
    id("org.jetbrains.kotlinx.benchmark") version "0.5.0"
}
allOpen { annotation("org.openjdk.jmh.annotations.State") }
benchmark { targets { register("main") } }
```

**Cost removed.** Separate harnesses per backend.

**Verify.** Not runnable here: Gradle is not installed on the machine
that produced this skill. The user runs `./gradlew benchmark`; this
snippet is unexecuted.

## Kotlin/Native and Kotlin/JS boundary

**Definition.** Kotlin/JVM, Kotlin/Native, and Kotlin/JS compile the same
source to different runtimes. JIT behavior, escape analysis, JMH numbers,
and `javap` output are JVM facts only. For example, JS and Wasm ignore
`lazy` modes ([lazy][lazy]).

**Use when.**

- The project targets Native or JS, and someone offers a JVM result as
  evidence.

**Do not use when.**

- The code is JVM-only; the rest of this skill applies directly.

**Example.** A multiplatform report states one row per target:

```text
target   harness                  result
jvm      JMH 1.37 (-prof gc)      measured
native   kotlinx-benchmark        not measured: konanc unavailable
js       kotlinx-benchmark        not measured
```

**Cost removed.** False transfer of JVM evidence to other backends.

**Verify.** Not runnable here: no Kotlin/Native compiler is installed,
and the catalog has no JS target. Measure each claimed target with its
own harness (kotlinx-benchmark) and state which targets are unmeasured.

[javap]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/javap.html
[whatsnew20]: https://kotlinlang.org/docs/whatsnew20.html
[threadmx]: https://docs.oracle.com/en/java/javase/25/docs/api/jdk.management/com/sun/management/ThreadMXBean.html
[javaman]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html
[jmh]: https://github.com/openjdk/jmh
[jmh35]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java
[cotest]: https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/
[jfrman]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/jfr.html
[kxbench]: https://github.com/Kotlin/kotlinx-benchmark
[lazy]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/lazy.html
