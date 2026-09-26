# Runtime configuration and interop constructs

Each card changes JVM flags, startup artifacts, or the native boundary.
Process-wide settings change every code path, so each card's verification
runs the whole program, not only a microbenchmark. Runnable pieces:
[`Workload.java`](../assets/examples/jmh/src/main/java/example/Workload.java),
[`Interop.java`](../assets/examples/jmh/src/main/java/example/Interop.java),
[`native_add.c`](../assets/examples/jmh/src/main/c/native_add.c),
`HeaderBench`, and `InteropBench`.

Measured on: Apple M1 Max (10 cores), macOS arm64, Homebrew OpenJDK
25.0.4.1, JMH 1.37, hyperfine; shared machine (load average 4 to 91).
Timings are machine-specific.

## Contents

- G1 default collector
- Generational ZGC
- Parallel GC for throughput
- AppCDS dynamic archive
- AOT cache
- AOT method profiles
- Compact object headers
- FFM downcalls instead of JNI
- Critical FFM downcalls
- Arena-scoped native memory

## G1 default collector

**Definition.** G1 is the default collector "on most hardware and
operating system configurations" and targets a pause-time goal,
`-XX:MaxGCPauseMillis`, default 200 ms ([collector selection][gc-select],
[G1 guide][g1]). With one available CPU, the JVM picks Serial instead.

**Use when.**

- No measured pause or throughput problem exists: the tuning guide
  advises to "first run your application and allow the VM to select a
  collector".
- Pauses exceed the goal: first lower allocation (the
  [allocation cards](allocation.md)), then adjust `-XX:MaxGCPauseMillis`
  or heap size and re-measure.

**Do not use when.**

- You assume G1 in a container with one CPU: locally
  `java -XX:ActiveProcessorCount=1 -Xlog:gc -version` printed
  `Using Serial`. Set `-XX:+UseG1GC` explicitly if G1 is required.
- You would set `-XX:MaxGCPauseMillis` very low to "fix" pauses without
  logs: the guide calls it a goal G1 meets "with high probability", and
  lower goals cost throughput.

**Example.**

```sh
java -Xmx256m -Xlog:gc,gc+phases:file=gc-G1.log \
  -cp target/benchmarks.jar example.Workload gc 3
java -XX:+PrintFlagsFinal -version | grep -E 'MaxGCPauseMillis|UseG1GC'
```

Local flags: `MaxGCPauseMillis = 200`, `UseG1GC = true {ergonomic}`.

**Cost removed.** None by itself; it is the baseline for every collector
change. Local `verify.sh tools` run: 3 s of `Workload gc`, `-Xmx256m`,
64 MiB retained, `Pause` lines from `-Xlog:gc,gc+phases`. The checksum is
bytes allocated, so higher means more work done.

| Collector | Pauses | Total pause | Max pause | Checksum |
| --- | --- | --- | --- | --- |
| G1 | 1,456 | 1,735.7 ms | 58.593 ms | 272,133,572,500 |
| ZGC | 1,255 | 6.3 ms | 0.100 ms | 382,676,482,500 |
| Parallel | 846 | 1,912.3 ms | 18.743 ms | 249,598,792,500 |

One run on a loaded machine: the ranking of pause totals is evidence,
the throughput column is not. Pause counts are not comparable across
collectors: ZGC logs several `Pause` phase lines per cycle (`Pause Mark
Start`, `Pause Mark End`, `Pause Relocate Start`), G1 one per pause.

**Verify.**

1. `sh assets/examples/verify.sh tools` fails unless the log starts with
   `Using G1`, and prints the pause summary.
1. Compare `pauses=`, `total=`, and `max=` against a candidate collector
   on the same workload and heap.

## Generational ZGC

**Definition.** ZGC does most of its work concurrently and keeps pauses
short. Since JDK 23 ([JEP 474][jep474]), `-XX:+UseZGC` is generational by
default. Since JDK 24 ([JEP 490][jep490]), the non-generational mode is
gone, and `-XX:+/-ZGenerational` only prints an obsolete-option warning.
The tuning guide describes max pauses under 1 ms and heaps from hundreds
of MB to 16 TB ([collector selection][gc-select]).

**Use when.**

- Tail latency is the objective, and G1 pause lines dominate it.
- There is CPU headroom for concurrent GC threads.

**Do not use when.**

- Throughput per core is the objective: the guide places ZGC at "further
  cost of throughput" relative to G1 ([G1 guide][g1]).
- You would compare ZGC to G1 by `-Xlog:gc` cycle times: ZGC `gc` lines
  are concurrent cycle durations, not pauses. Use `gc+phases` `Pause`
  lines.

**Example.**

```sh
java -XX:+UseZGC -Xmx256m -Xlog:gc,gc+phases:file=gc-Z.log \
  -cp target/benchmarks.jar example.Workload gc 3
```

**Cost removed.** Stop-the-world time. See the collector table in the
[G1 card](#g1-default-collector).

**Verify.**

1. `sh assets/examples/verify.sh tools` requires the banner
   `Using The Z Garbage Collector` and prints `Pause` statistics from
   `gc+phases`.
1. In an application, compare request latency percentiles and CPU time,
   not only pause lines.

## Parallel GC for throughput

**Definition.** `-XX:+UseParallelGC` collects with stop-the-world
parallel threads. The tuning guide recommends it when "peak application
performance" matters and pauses of a second or longer are acceptable
([collector selection][gc-select]).

**Use when.**

- Batch jobs, builds, or offline processing, where total run time matters
  and no request waits on a pause.

**Do not use when.**

- Any request path has a latency objective: full collections pause all
  application threads (`Pause Full` lines in the log).

**Example.**

```sh
java -XX:+UseParallelGC -Xmx256m -Xlog:gc:file=gc-Parallel.log \
  -cp target/benchmarks.jar example.Workload gc 3
```

**Cost removed.** G1's concurrent work: the G1 guide notes G1 "may
exhibit higher overhead than the above collectors, affecting throughput
due to its concurrent nature" ([G1 guide][g1]). Measure it as job wall
time and process CPU time for the same input; pause lines show the
price.

**Verify.**

1. `sh assets/examples/verify.sh tools` requires `Using Parallel` and
   prints the pause summary. The `Workload gc` checksum line reports the
   work done in the fixed time.

## AppCDS dynamic archive

**Definition.** Class Data Sharing maps pre-parsed class metadata from an
archive. The JDK ships a default archive for JDK classes (on since
JDK 12, [JEP 341][jep341]). `-XX:ArchiveClassesAtExit=app.jsa` writes a
dynamic archive of the classes a run loaded, application classes
included, and `-XX:SharedArchiveFile=app.jsa` uses it (JDK 13+,
[JEP 350][jep350]).

**Use when.**

- Startup or short-lived processes (CLI tools, functions, test forks)
  dominate, and class loading shows in startup profiles.
- The JDK is below 24, so the AOT cache is unavailable.

**Do not use when.**

- The JDK is 25+ and you can do a training run: the
  [AOT cache](#aot-cache) archives the same classes plus linking and, on
  JDK 25, profiles.
- Application classes come from a directory class path: JEP 483 requires
  JAR class paths for the AOT cache, and this skill verified AppCDS only
  with a JAR. Before claiming a gain, check that the `-Xlog:class+load`
  line for an application class shows `shared objects file (top)`.

**Example.**

```sh
java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar example.Workload startup
java -XX:SharedArchiveFile=app.jsa -Xlog:class+load \
  -cp app.jar example.Workload startup | grep 'example.Workload '
```

Local log line: `example.Workload source: shared objects file (top)`.

**Cost removed.** Class parsing and verification at startup. Local
`verify.sh startup` (hyperfine, 30 runs, shared machine):

| Run | Classes loaded | From archive | Mean | User CPU |
| --- | --- | --- | --- | --- |
| `-Xshare:off` | 809 | 0 | 93.3 ± 13.2 ms | 86.6 ms |
| default CDS | 796 | 792 | 46.8 ± 6.7 ms | 41.8 ms |
| AppCDS `app.jsa` | 729 | 728 | 39.0 ± 1.1 ms | 29.5 ms |
| AOT cache `app.aot` | 857 | 857 | 34.6 ± 6.3 ms | 22.5 ms |

The `Workload startup` program is tiny (a stream over three strings);
gains scale with the number of application classes.

**Verify.**

1. `sh assets/examples/verify.sh startup` fails unless
   `example.Workload source: shared objects file (top)` appears.
1. The same mode prints loaded and shared class counts and a `hyperfine`
   comparison. Compare `User` CPU time as well as mean wall time.

## AOT cache

**Definition.** The AOT cache ([JEP 483][jep483], JDK 24) stores classes
that a training run already loaded and linked. JDK 24 needs two steps
(`-XX:AOTMode=record -XX:AOTConfiguration=app.aotconf`, then
`-XX:AOTMode=create`); JDK 25 adds the one-step
`-XX:AOTCacheOutput=app.aot` ([JEP 514][jep514]). Production runs pass
`-XX:AOTCache=app.aot`.

**Use when.**

- Startup time matters, and you can run a representative training
  workload at build time with the same JDK, OS, and CPU architecture.

**Do not use when.**

- The production JDK build, OS, or architecture differs from the training
  run, or the class path differs other than by appended entries: JEP 483
  requires them to match. On a mismatch, HotSpot "issues a warning
  message and continues" without the cache.
- The class path contains directories (JEP 483 does not support them).
- You need a stale cache to fail the launch: add `-XX:AOTMode=on`. On
  25.0.4.1, a missing cache with `-XX:AOTMode=on` stopped the JVM with
  `Unable to map shared spaces`. This JDK rejects `-XX:AOTMode=required`
  ("Must be one of the following: off, record, create, auto, on").

**Example.**

```sh
java -XX:AOTCacheOutput=app.aot -cp app.jar example.Workload startup
java -XX:AOTCache=app.aot -XX:AOTMode=on -cp app.jar \
  example.Workload startup
```

The first command runs the program, then launches a child JVM
("Launching child process ... to assemble AOT cache"). Locally it
printed `AOTCache creation is complete: app.aot 10469376 bytes`.

**Cost removed.** Class loading and linking during startup. JEP 483
reports HelloStream 0.031 s to 0.018 s and Spring PetClinic 4.486 s to
2.604 s on its test machine. Local numbers are in the
[AppCDS table](#appcds-dynamic-archive).

**Verify.**

1. `sh assets/examples/verify.sh startup` runs the program with
   `-XX:AOTCache=app.aot -XX:AOTMode=on` (fails if the cache is unusable)
   and prints class counts: every class must be
   `source: shared objects file`.
1. The `hyperfine` rows compare default CDS, AppCDS, and the AOT cache.

## AOT method profiles

**Definition.** On JDK 25, [JEP 515][jep515] stores method execution
profiles from the training run in the AOT cache, so the JIT can compile
hot methods with profile data from startup. It adds no flags; the
existing cache commands include it.

**Use when.**

- Time to peak performance (warmup), not only startup, is the objective,
  and the training run exercises the hot paths production uses.

**Do not use when.**

- The training workload differs from production: the profiles then steer
  early compilation toward the wrong paths. JEP 515 depends on the
  training run representing the application.
- You cannot re-train on each release: stale caches do not match the new
  class path (see [AOT cache](#aot-cache)).

**Example.** The [AOT cache](#aot-cache) commands, plus the diagnostic
flags that show profiles being recorded and replayed. The training run
must execute the hot path long enough to be profiled.

```sh
java -XX:AOTCacheOutput=app.aot \
  -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal \
  -cp app.jar example.Workload startup | grep AOTRecordTraining
java -XX:AOTCache=app.aot -XX:AOTMode=on \
  -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal \
  -cp app.jar example.Workload startup | grep AOTReplayTraining
```

On JDK 25.0.4.1, the first command printed `AOTRecordTraining = true`
for the training JVM and `false` for the child JVM that assembles the
cache; the second printed `AOTReplayTraining = true`.

**Cost removed.** Profiling time during warmup. JEP 515 reports a stream
example dropping from 90 ms to 73 ms (19%) with about 250 KB more cache.

**Verify.** Tier: **executed (mechanism), benefit not measured**. With
`-XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal`, the local training
run reported `AOTRecordTraining = true {ergonomic}`, and the production
run with `-XX:AOTCache=app.aot` reported `AOTReplayTraining = true
{ergonomic}`. The `Workload startup` program is too short to have hot
methods, so no warmup gain is claimed. Measure time-to-throughput (for
example, requests completed in the first N seconds) with and without
`-XX:AOTCache`.

## Compact object headers

**Definition.** `-XX:+UseCompactObjectHeaders` (a product flag in JDK 25,
[JEP 519][jep519]) shrinks the object header on 64-bit HotSpot. The
`java` manual states that it saves 4 bytes per object on average and is
off by default ([java][java-man]).

**Use when.**

- Many small objects dominate the heap (check instance counts with
  `jcmd <pid> GC.class_histogram`), and the JDK is 25+.

**Do not use when.**

- Objects are large arrays: the saving is per object, not per element.
- Alignment absorbs the saving for a given shape: object sizes round up
  to 8 bytes, so measure each hot shape.

**Example.**

```java
@Benchmark
public Object twoIntsDefault() {
    return new Workload.TwoInts();          // two int fields
}

@Benchmark
@Fork(value = 2, jvmArgsAppend = "-XX:+UseCompactObjectHeaders")
public Object twoIntsCompact() {
    return new Workload.TwoInts();
}
```

Runnable: `HeaderBench.java`.

**Cost removed.** Header bytes per object. Measured `gc.alloc.rate.norm`:
`new Object()` 16 to 8 B; two `int` fields 24 to 16 B. JEP 519 reports
22% less heap and 8% less CPU time on SPECjbb2015 in its tests.

**Verify.**

1. `sh assets/examples/verify.sh measure` asserts that `objectCompact`
   and `twoIntsCompact` allocate less per operation than the defaults,
   and prints the `# VM options:` lines showing the flag.
1. For an application, compare `jcmd <pid> GC.heap_info` after the same
   load, or the live-set size from `-Xlog:gc` after full collections.

## FFM downcalls instead of JNI

**Definition.** The Foreign Function and Memory API (final in JDK 22,
[JEP 454][jep454]) calls native functions through a `MethodHandle` from
`Linker.nativeLinker().downcallHandle(symbol, FunctionDescriptor)`, with
no C glue code; `Arena` scopes native memory. Downcall creation is a
restricted method: since JDK 22 it warns without
`--enable-native-access=ALL-UNNAMED` (or a module name)
([JEP 454][jep454]). JDK 24 extended the same warning to JNI's
`System.load` and `System.loadLibrary` ([JEP 472][jep472]). Locally, the
first restricted call printed `WARNING: A restricted method in
java.lang.foreign.Linker has been called`.

**Use when.**

- Writing new native bindings, or replacing JNI code whose C wrappers
  only forward arguments.
- The JNI glue is a maintenance or build cost (per-platform compilation
  of wrapper code).

**Do not use when.**

- The target JDK is below 22 (preview only in 19 to 21).
- The native function calls back into Java many times per call: upcalls
  have their own cost, so measure them.

**Example.**

```java
private static final Linker LINKER = Linker.nativeLinker();
private static final MethodHandle STRLEN = LINKER.downcallHandle(
    LINKER.defaultLookup().find("strlen").orElseThrow(),
    FunctionDescriptor.of(JAVA_LONG, ADDRESS));

public static long strlen(String s) {
    try (Arena arena = Arena.ofConfined()) {
        MemorySegment str = arena.allocateFrom(s);  // UTF-8, NUL added
        return (long) STRLEN.invokeExact(str);
    } catch (Throwable t) {
        throw new IllegalStateException(t);
    }
}
```

Runnable: `Interop.java`. `javac -Xlint:all` warns on every restricted
call ("is a restricted method"); the example opts in with
`@SuppressWarnings("restricted")`.

**Cost removed.** The C wrapper per function (one JNI function in
`native_add.c` versus none). Call overhead for `int add(int, int)`, two
runs (1 then 3 forks): `jni` 3.313 ± 0.469 and 4.001 ± 0.800 ns/op;
`ffm` 2.773 ± 0.375 and 2.991 ± 0.609 ns/op; plain Java `x + y` 0.584
and 0.616 ns/op. FFM versus JNI: **no measurable difference** (intervals
overlap in both runs). The benefit is removing the C wrapper, not speed.

**Verify.**

1. `sh assets/examples/verify.sh verify` compares `jniAdd`, `ffmAdd`, and
   `ffmAddCritical` with Java `+` on overflow inputs, and checks
   `strlen("héllo") == 6` (UTF-8 bytes).
1. `BENCH_FILTER=InteropBench sh assets/examples/verify.sh measure`
   compares call cost.

## Critical FFM downcalls

**Definition.** `Linker.Option.critical(boolean allowHeapAccess)`
(JDK 22) marks a downcall as critical: "extremely short running time in
all cases" and no callbacks into Java ([Linker.Option][linker-option]).
With `allowHeapAccess` true, heap segments can be passed directly.

**Use when.**

- The native function is tiny, never blocks, and never calls Java, and
  the transition cost shows in a profile.

**Do not use when.**

- The function may block, run long, or call back into Java: the javadoc
  warns that misuse can cause "loss of performance or JVM crashes".

**Example.**

```java
ADD_CRITICAL = LINKER.downcallHandle(add, INT_INT_INT,
    Linker.Option.critical(false));
```

**Cost removed.** Thread-state transition work around the call.
Measured: `ffmCritical` 2.030 ± 0.209 and 2.029 ± 0.058 ns/op versus
`ffm` 2.773 ± 0.375 and 2.991 ± 0.609 ns/op (two runs, intervals
separate).

**Verify.**

1. Same oracle as the previous card (`ffmAddCritical` must equal `+`).
1. `InteropBench.ffmCritical` versus `InteropBench.ffm`.

## Arena-scoped native memory

**Definition.** `Arena.ofConfined()` allocates native memory owned by one
thread and frees all of it when the arena closes. Any later access to its
segments throws `IllegalStateException` ([Arena][arena]).

**Use when.**

- Native buffers have a clear lifetime (one call, one request) and
  currently use `ByteBuffer.allocateDirect`, whose memory is freed only
  after the GC collects the buffer object.

**Do not use when.**

- Several threads must use the memory: use `Arena.ofShared()`. Access to
  a confined segment from another thread throws `WrongThreadException`.
- The lifetime is unknown: `Arena.ofAuto()` leaves freeing to the GC, like
  a direct buffer.

**Example.**

```java
MemorySegment seg;
try (Arena arena = Arena.ofConfined()) {
    seg = arena.allocate(JAVA_INT);
    seg.set(JAVA_INT, 0, 42);
}
seg.get(JAVA_INT, 0);   // IllegalStateException: already closed
```

Runnable: `Interop.closedSegment()`.

**Cost removed.** Native memory held until a GC runs. The benefit is a
deterministic free at `close()`; the card makes no timing claim.

**Verify.**

1. `sh assets/examples/verify.sh verify` asserts that the access after
   close throws `IllegalStateException`.

[gc-select]: https://docs.oracle.com/en/java/javase/25/gctuning/available-collectors.html
[g1]: https://docs.oracle.com/en/java/javase/25/gctuning/garbage-first-g1-garbage-collector1.html
[jep474]: https://openjdk.org/jeps/474
[jep490]: https://openjdk.org/jeps/490
[jep341]: https://openjdk.org/jeps/341
[jep350]: https://openjdk.org/jeps/350
[jep483]: https://openjdk.org/jeps/483
[jep514]: https://openjdk.org/jeps/514
[jep515]: https://openjdk.org/jeps/515
[jep519]: https://openjdk.org/jeps/519
[jep454]: https://openjdk.org/jeps/454
[jep472]: https://openjdk.org/jeps/472
[java-man]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html
[linker-option]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/foreign/Linker.Option.html#critical(boolean)
[arena]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/foreign/Arena.html
