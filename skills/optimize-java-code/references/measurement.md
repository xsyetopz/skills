# Measurement constructs

Each card is a tool or harness construct that attributes a cost or proves
that it moved. The runnable project is
[`assets/examples/jmh`](../assets/examples/jmh) (Maven, JMH 1.37, JDK 25);
[`verify.sh`](../assets/examples/verify.sh) builds it in a temporary copy.

Measured on: Apple M1 Max, macOS arm64, Homebrew OpenJDK 25.0.4.1, Maven
3.9.16, JMH 1.37. Other jobs shared the machine (load average 4 to 91
during runs), so timings are machine-specific and noisy. Byte counts per
operation are deterministic for a given JDK and input.

## Contents

- JMH benchmark anatomy
- Consuming results in JMH
- JMH GC profiler and alloc rate norm
- Comparing JMH JSON results
- JDK Flight Recorder
- jcmd on a live JVM
- async-profiler
- Unified GC logging
- JIT compilation and inlining logs

## JMH benchmark anatomy

**Definition.** [JMH](https://github.com/openjdk/jmh) generates a harness
around each `@Benchmark` method. `@State` objects hold inputs (scope
`Thread`, `Benchmark`, or `Group`). `@Setup(Level.Trial|Iteration|
Invocation)` builds them outside the timed region. `@Fork` runs each
benchmark in fresh JVMs, and `@Warmup`/`@Measurement` set iteration
counts and times so the result reflects the JIT-compiled steady state.

**Use when.**

- The question is the steady-state cost of one isolated operation (a
  method, a data structure choice, a construct card's pair).
- Baseline and candidate can run on the same inputs in the same JVM
  configuration.

**Do not use when.**

- The question is startup, first-request latency, or an end-to-end
  service metric: JMH warmup hides exactly that cost. Use
  [unified GC logging](#unified-gc-logging), [JFR](#jdk-flight-recorder),
  or `hyperfine` on the real launch command.
- Inputs are built inside the `@Benchmark` method: their allocation and
  time are then measured too. Build them in `@Setup(Level.Trial)`.
- The benchmark takes less than a millisecond per call and you plan
  `@Setup(Level.Invocation)`: the `Level` javadoc restricts that level to
  calls longer than a millisecond, because per-call timestamping
  saturates small benchmarks ([Level javadoc][jmh-level]).
- You would report a result from `-f 0` (no fork): the harness and
  benchmark then share one JVM and one profile
  ([JMHSample_12_Forking][sample12]).

**Example.**

```java
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Fork(value = 2, jvmArgsAppend = {"-Xms1g", "-Xmx1g"})
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
public class AllocationBench {
    private List<String> parts;

    @Setup(Level.Trial)
    public void setup() {
        parts = new ArrayList<>();
        for (int i = 0; i < 64; i++) {
            parts.add("part" + i);
        }
    }

    @Benchmark
    public String stringLoopBuilder() {
        return Allocation.Strings.loopBuilder(parts);
    }
}
```

Runnable: `AllocationBench.java`. The `pom.xml` wires the annotation
processor through `annotationProcessorPaths` and shades
`org.openjdk.jmh.Main` into `target/benchmarks.jar`. Check that
`META-INF/BenchmarkList` is in the jar (`unzip -l target/benchmarks.jar |
grep BenchmarkList`): since JDK 23, javac no longer runs processors found
on the class path implicitly ([JDK-8321314][jdk-8321314]).

Command-line options override annotations. Locally,
`java -jar target/benchmarks.jar escapeLocalNoEA -jvmArgsAppend -Dx=1`
printed `# VM options: -Djava.io.tmpdir=... -Dx=1`: JMH silently dropped
the method's
`@Fork(jvmArgsAppend = {"-Xms1g", "-Xmx1g", "-XX:-DoEscapeAnalysis"})`.
With `-jvmArgs "-Dnative.lib=..."` instead, the line was
`# VM options: -Dnative.lib=... -Xms1g -Xmx1g -XX:-DoEscapeAnalysis`.
Pass shared options with `-jvmArgs`, and read every `# VM options:` line.

**Cost removed.** Measurement error, not program cost: JIT warmup,
profile pollution between benchmarks, and setup work inside the timed
region. It shows as a shrinking `Error` column (99.9% confidence
half-width) and stable scores across forks.

**Verify.**

1. `sh assets/examples/verify.sh benchmark` runs every benchmark once
   (`-f 1 -wi 0 -i 1 -r 100ms`) and fails on any benchmark error
   (`-foe true`). It proves the harness, not a timing.
1. `sh assets/examples/verify.sh measure` prints
   `grep '^# VM options:' | sort | uniq -c`; every expected per-benchmark
   flag must appear there.

## Consuming results in JMH

**Definition.** C2 removes computations whose results are unused
(dead-code elimination) and computes expressions over constants at
compile time (constant folding). JMH defeats both when the benchmark
returns its result or passes it to `Blackhole.consume`, and when inputs
come from non-final `@State` fields ([JMHSample_08_DeadCode][sample08],
[JMHSample_09_Blackholes][sample09],
[JMHSample_10_ConstantFold][sample10]).

**Use when.**

- Every benchmark: return the result, or, when there are several values,
  consume each with a `Blackhole` parameter.

**Do not use when.**

- Do not sum results into a field, or loop inside the benchmark to
  "amplify" the work: the JIT can hoist, unroll, or vectorize the loop,
  as [JMHSample_11_Loops][sample11] documents. Use
  `@OperationsPerInvocation` only when the loop itself is the workload.

**Example.**

```java
private double x = Math.PI;                // non-final: not a constant
private static final double CONSTANT = Math.PI;

@Benchmark
public void wrongDiscarded() {
    Math.log(x);                           // result unused
}

@Benchmark
public double wrongConstant() {
    return Math.log(CONSTANT);             // folded at compile time
}

@Benchmark
public double rightReturned() {
    return Math.log(x);
}

@Benchmark
public void rightBlackhole(Blackhole bh) {
    bh.consume(Math.log(x));
    bh.consume(Math.log(x + 1));
}
```

Runnable: `HarnessBench.java`.

**Cost removed.** False speedups. The bug's signature: a `wrong*` score
equal to the empty `baseline` benchmark. See the local results below.

**Verify.**

1. `BENCH_FILTER=HarnessBench sh assets/examples/verify.sh measure`.
1. `wrongDiscarded` and `wrongConstant` must be near `baseline`;
   `rightReturned` must be clearly above it. A candidate benchmark that
   scores near `baseline` is not measuring the work.

### Local harness results

`BENCH_FILTER=HarnessBench FORKS=3 sh assets/examples/verify.sh measure`
(3 forks x 5 iterations; `work` is 16 dependent divisions):

| Benchmark | ns/op | Reading |
| --- | --- | --- |
| `baseline` (empty) | 0.611 ± 0.044 | harness floor |
| `wrongDiscarded` | 0.607 ± 0.019 | work deleted |
| `wrongConstant` | 0.621 ± 0.020 | work folded |
| `rightReturned` | 16.375 ± 4.738 | work measured |
| `rightBlackhole` (2 calls) | 23.825 ± 0.926 | work measured |
| `logDiscarded` | 6.801 ± 0.590 | not deleted here |
| `logReturned` | 7.057 ± 0.164 | measured |

The JMH sample's own `Math.log` case was **not** eliminated on JDK 25
arm64 (`logDiscarded` equals `logReturned`). A benchmark that happens to
survive on one JVM does not prove the pattern safe. JMH also printed
`# Blackhole mode: compiler (auto-detected ...)`: on this JDK it uses
the C2 blackhole intrinsic.

## JMH GC profiler and alloc rate norm

**Definition.** `-prof gc` adds secondary results read from GC MXBeans:
`gc.alloc.rate` (MB/s), `gc.alloc.rate.norm` (bytes allocated per
benchmark operation), `gc.count`, and `gc.time`
([JMHSample_35_Profilers][sample35]). Compare `gc.alloc.rate.norm`: it
is independent of speed.

**Use when.**

- A card claims fewer allocations (escape analysis, presizing, boxing,
  string building): only `gc.alloc.rate.norm` proves the claim.

**Do not use when.**

- The question is retained (live) memory: allocation per operation says
  nothing about what survives. Use `jcmd <pid> GC.class_histogram` or a
  heap dump ([jcmd on a live JVM](#jcmd-on-a-live-jvm)).
- You compare `gc.alloc.rate` (MB/s): it rises when a candidate gets
  faster at the same bytes per operation.

**Example.**

```sh
java -jar target/benchmarks.jar 'AllocationBench.escape' \
  -f 1 -wi 3 -i 5 -prof gc -rf json -rff jmh.json
```

Local output (machine-specific):

```text
AllocationBench.escapeLocal:gc.alloc.rate.norm      avgt  0.015  B/op
AllocationBench.escapeLocalNoEA:gc.alloc.rate.norm  avgt  24000.084  B/op
```

Values like `0.015` or `≈ 10⁻⁴` B/op are harness noise: treat anything
below 1 B/op as zero.

**Cost removed.** The observation tool for every allocation card: bytes
per operation must drop for the candidate.

**Verify.**

1. The JSON row has `secondaryMetrics["gc.alloc.rate.norm"].score`;
   `python3 scripts/jmh_compare.py jmh.json` prints it as `alloc B/op`.
1. `jmh_compare.py jmh.json --alloc-lower BASE:CAND` exits 1 unless the
   candidate is at least 10% below the baseline.

## Comparing JMH JSON results

**Definition.** `scripts/jmh_compare.py` reads JMH `-rf json` output.
With one file, it prints every row (score, 99.9% error, unit,
`gc.alloc.rate.norm`) and checks named baseline:candidate pairs. With two
files, it matches rows by benchmark, mode, threads, and params, and labels
each ratio `within error` when the two confidence intervals overlap.

**Use when.**

- Comparing a baseline run and a candidate run of the same benchmarks
  (for example, before and after a commit, or two JVM flag sets).
- Asserting an allocation claim in CI.

**Do not use when.**

- The files come from different machines, JDKs, or benchmark code: the
  script checks row identity, not environment. Record the environment.
- A run had one iteration: `scoreError` is `NaN`, and every comparison
  reports `within error`.

**Example.**

```sh
python3 scripts/jmh_compare.py base.json cand.json --fail-regression 5
python3 scripts/jmh_compare.py jmh.json \
  --alloc-lower listDefault:listPresized \
  --alloc-same stringExprBuilder:stringExprConcat
```

**Cost removed.** Hand comparison errors: mismatched rows, unit mix-ups,
and calling a difference inside the error bars a win.

**Verify.**

1. `python3 scripts/test_jmh_compare.py` (stdlib only) covers parsing,
   identity mismatch, `NaN` errors, throughput direction, and exit codes.
1. Exit codes: 0 pass, 1 check failed, 2 invalid input.

## JDK Flight Recorder

**Definition.** JFR is the JVM's built-in event recorder. Start it with
`-XX:StartFlightRecording` (parameters `filename`, `duration`,
`settings`, `dumponexit`), and read the file with the `jfr` tool:
`summary`, `print
--events`, and `view` ([java][java-man], [jfr][jfr-man]).
`settings=profile` samples more often than the default settings, at
higher overhead.

**Use when.**

- You need to attribute CPU (`jdk.ExecutionSample`), allocation
  (`jdk.ObjectAllocationSample`), GC pauses (`jdk.GCPhasePause`), lock
  waits (`jdk.JavaMonitorEnter`), or virtual thread pinning
  (`jdk.VirtualThreadPinned`) in a real application run.

**Do not use when.**

- You need a per-operation number: JFR samples rather than counting
  every call. Use JMH for that.
- You would read `jfr view hot-methods` as inclusive time: `jfr view --verbose
  hot-methods` shows that it groups by `stackTrace.topFrame` (self
  samples).

**Example.**

```sh
java -XX:StartFlightRecording=filename=rec.jfr,settings=profile \
  -cp target/benchmarks.jar example.Workload gc 3
jfr summary rec.jfr
jfr view hot-methods rec.jfr
jfr view allocation-by-class rec.jfr
jfr view gc-pauses rec.jfr
jfr print --events jdk.ObjectAllocationSample --stack-depth 5 rec.jfr
```

Local `jfr summary` excerpt for a 3-second run (event, count, bytes):

```text
jdk.ObjectAllocationSample                900         13394
jdk.ExecutionSample                        49           489
jdk.GCPhasePause                           35           795
```

**Cost removed.** Guessing the hotspot. The recording names the dominant
method and allocation site; a candidate matters only if it touches them.

**Verify.**

1. `sh assets/examples/verify.sh tools` records, then fails unless
   `jfr summary` lists `jdk.ExecutionSample`.
1. After a change, re-record the same workload and compare the same view
   (for example, the target method's share in `hot-methods`).

## jcmd on a live JVM

**Definition.** `jcmd <pid> <command>` sends diagnostic commands to a
running JVM: `VM.version`, `VM.flags`, `GC.class_histogram`,
`GC.heap_info`, `Thread.print`, `JFR.start`, `JFR.dump`, `JFR.stop`
([jcmd][jcmd-man]).

**Use when.**

- The process is already running (a service) and cannot restart with new
  flags.
- You need live-object counts by class (`GC.class_histogram`) to check a
  retention claim, or the effective flags (`VM.flags`) of a deployment.

**Do not use when.**

- The process serves latency-sensitive traffic and you plan
  `GC.class_histogram`: `jcmd <pid> help GC.class_histogram` reports
  "Impact: High: Depends on Java heap size and content", and without
  `-all` it inspects only reachable objects. Run it on a canary or in a
  test.

**Example.**

```sh
jcmd <pid> VM.flags
jcmd <pid> GC.class_histogram | head
jcmd <pid> JFR.start name=live settings=profile
jcmd <pid> JFR.dump name=live filename=/tmp/live.jfr
jcmd <pid> JFR.stop name=live
```

**Cost removed.** A restart to collect evidence. Read the dumped
recording with `jfr summary`.

**Verify.**

1. `sh assets/examples/verify.sh tools` starts `Workload wait 30`, runs
   `VM.version`, `GC.class_histogram`, `JFR.start`, and `JFR.dump`, and
   prints the dumped recording's summary.

## async-profiler

**Definition.** [async-profiler]
is a sampling profiler for HotSpot JVMs on Linux and macOS (x64 and
arm64) that samples CPU, allocations, locks, or wall-clock time. Its
README states it "does not suffer from the Safepoint bias problem". It
writes flame graphs: `asprof -d 30 -f flamegraph.html <pid>`.

**Use when.**

- You need a CPU or wall-time flame graph including native and JVM
  frames, or allocation flame graphs by call site.

**Do not use when.**

- It is not installed and cannot be: JFR covers CPU and allocation
  sampling with no install.

**Example.** The event names are those listed by the JMH wrapper
(`-prof async:help`: `cpu, alloc, lock, wall, itimer`).

```sh
asprof -d 30 -e cpu -f cpu.html <pid>
asprof -d 30 -e alloc -f alloc.html <pid>
java -jar target/benchmarks.jar 'CodegenBench' \
  -prof async:libPath=/path/to/libasyncProfiler.dylib\;output=flamegraph
```

**Cost removed.** Same as JFR, with native frames visible.

**Verify.** Tier: **not runnable here**. async-profiler is not installed
on the measuring machine: `java -jar target/benchmarks.jar -lprof`
reported `async: <none>` ("Unable to load async-profiler"). The `perf`,
`perfasm`, and `perfnorm` JMH profilers are also unavailable (no `perf`
on macOS), and `dtraceasm` requires `sudo`. The commands above are
unexecuted.

## Unified GC logging

**Definition.** `-Xlog:gc` prints one line per collection with cause,
heap before and after, and duration. `-Xlog:gc,gc+phases` adds per-phase
lines, including ZGC's
`Pause Mark Start`/`Pause Mark End`/`Pause Relocate Start`.
`-Xlog:gc*:file=gc.log` sends output to a file ([java][java-man]).

**Use when.**

- Comparing collectors or heap settings: pause count, total, and maximum
  come straight from the log.
- Checking which collector a deployment actually runs: the first line is
  `Using G1`, `Using Parallel`, `Using Serial`, or `Using The Z Garbage
  Collector`.

**Do not use when.**

- You compare ZGC and G1 by `-Xlog:gc` alone: ZGC's `gc` lines report
  whole concurrent cycles (for example `Major Collection (Warmup) ...
  0.003s`), not pauses. Add `gc+phases` and compare `Pause` lines.

**Example.**

```sh
java -XX:+UseZGC -Xmx256m -Xlog:gc,gc+phases:file=gc-Z.log \
  -cp target/benchmarks.jar example.Workload gc 3
```

Local lines (machine-specific):

```text
[0.006s][info][gc] Using G1
[0.039s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause)
  48M->5M(256M) 1.015ms
[0.037s][info][gc,phases] GC(0) Y: Pause Mark Start (Major) 0.006ms
```

`java -XX:ActiveProcessorCount=1 -Xlog:gc -version` printed
`Using Serial`: with one CPU the JVM does not treat the machine as server
class and picks Serial, which matters in small containers.

**Cost removed.** Unverified collector assumptions. The metric is the
pause distribution per collector on the same workload.

**Verify.**

1. `sh assets/examples/verify.sh tools` runs the workload under G1, ZGC,
   and Parallel, fails if the `Using ...` banner is missing, and prints
   `pauses=N total=...ms max=...ms` per collector.

## JIT compilation and inlining logs

**Definition.** `-XX:+PrintCompilation` prints a line per compiled
method: timestamp, compile id, `%` for on-stack replacement, tier (1 to 3
C1, 4 C2), and `made not entrant` on deoptimization ([java][java-man]).
`-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` prints each call
site decision (`inline (hot)`, `too big`, `failed to inline: ...`).

**Use when.**

- A benchmark result depends on inlining or escape analysis (the callee
  must inline for scalar replacement).
- You suspect deoptimization loops (`made not entrant` repeating).

**Do not use when.**

- You need machine code: `-XX:+PrintAssembly` needs the `hsdis` plugin,
  which the JDK does not ship and which was not installed here, so it is
  not runnable on this machine.

**Example.**

```sh
java -XX:+PrintCompilation -cp target/benchmarks.jar example.Workload jit \
  | grep 'Escape::local'
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining \
  -cp target/benchmarks.jar example.Workload jit | grep lengthSquared
```

Local output (abridged):

```text
42   70 %     4       example.Allocation$Escape::local @ 4 (39 bytes)
44   71       4       example.Allocation$Escape::local (39 bytes)
@ 26   example.Allocation$Escape$Point::lengthSquared (24 bytes)   inline (hot)
```

Defaults on this JDK (`java -XX:+PrintFlagsFinal -version`):
`MaxInlineSize = 35`, `FreqInlineSize = 325` bytecode bytes.

**Cost removed.** Guessing whether the JIT inlined or compiled a method.

**Verify.**

1. `sh assets/examples/verify.sh tools` fails unless `Escape::local` is
   compiled and `lengthSquared (24 bytes)   inline (hot)` appears.

[jmh-level]: https://github.com/openjdk/jmh/blob/master/jmh-core/src/main/java/org/openjdk/jmh/annotations/Level.java
[sample08]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_08_DeadCode.java
[sample09]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_09_Blackholes.java
[sample10]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_10_ConstantFold.java
[sample11]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_11_Loops.java
[sample12]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_12_Forking.java
[sample35]: https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java
[jdk-8321314]: https://bugs.openjdk.org/browse/JDK-8321314
[java-man]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html
[jfr-man]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/jfr.html
[jcmd-man]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html

[async-profiler]: https://github.com/async-profiler/async-profiler
