---
name: optimize-java-code
description: >-
  Profiles and optimizes Java CPU time, allocation, latency, and startup with
  JMH, JFR, and GC and JIT logs. Use when a Java benchmark or profile shows
  the cost. Not for Kotlin or Scala code.
---

# Optimize Java Code

Make a measured Java hot path or JVM configuration cheaper without changing
observable behavior. Each change applies one reference card to a cost that
JFR, JMH, or a GC/JIT log attributes, is checked by an equivalence oracle,
and is kept only if the metric the card names improves. Several cards
report **no measurable difference** because C2 already optimizes the
baseline, so read the card before applying a construct.

## Workflow

1. Record the target: `java -version`, the build's `--release`/
   `maven.compiler.release` (or Gradle toolchain), the production JVM flags,
   and `java -XX:+PrintFlagsFinal -version` values the card depends on
   (collector, `MaxInlineSize`, `UseCompactObjectHeaders`). Keep the JDK
   and language level; a construct that needs a newer JDK is a separate,
   user-approved change.
1. Reproduce the workload with production flags. Pick the metric the user
   cares about: mean or tail latency, throughput, bytes per operation, GC
   pause, heap footprint, startup, or time to peak.
1. Attribute the cost before editing
   ([measurement](references/measurement.md)):
   - application CPU or allocation: JFR with `settings=profile`, then
     `jfr view hot-methods` and `jfr view allocation-by-class`;
   - running service: `jcmd <pid> JFR.start` / `JFR.dump`,
     `GC.class_histogram` for retention;
   - GC pauses: `-Xlog:gc,gc+phases`;
   - one isolated method: a JMH benchmark with `-prof gc`.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty, boundary, overflow, `null`, Unicode, and exception
   cases, in the project's test framework. `Verify.java` in the examples
   shows the minimum.
1. Apply the change, then run the card's **Verify** steps: behavior
   first, then the named metric. Per-operation allocation claims use
   `gc.alloc.rate.norm` from JMH forks (steady-state C2 code); an
   in-process allocation delta is valid only for objects that are stored
   (so escape analysis cannot remove them), such as footprint checks.
1. Compare runs with `scripts/jmh_compare.py` and re-run the
   application-level workload. Keep the change only when the target metric
   moved beyond the error bars and nothing else regressed; revert
   otherwise.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| Need a trustworthy microbenchmark | [JMH anatomy](references/measurement.md#jmh-benchmark-anatomy), [consuming results](references/measurement.md#consuming-results-in-jmh) |
| Need bytes per operation | [JMH -prof gc](references/measurement.md#jmh-gc-profiler-and-alloc-rate-norm), [comparing results](references/measurement.md#comparing-jmh-json-results) |
| Unknown hotspot in an app | [JFR](references/measurement.md#jdk-flight-recorder), [jcmd](references/measurement.md#jcmd-on-a-live-jvm), [async-profiler](references/measurement.md#async-profiler) |
| GC pauses or collector unknown | [GC logging](references/measurement.md#unified-gc-logging) |
| Inlining or deopt questions | [JIT logs](references/measurement.md#jit-compilation-and-inlining-logs) |
| Small temporaries allocated per call | [Escape analysis](references/allocation.md#escape-analysis-and-scalar-replacement), [escaping temporaries](references/allocation.md#escaping-temporaries) |
| `s = s + x` in a loop | [StringBuilder](references/allocation.md#stringbuilder-for-loop-concatenation) |
| Request to replace `a + b + c` with a builder | [Single-expression concat](references/allocation.md#single-expression-concatenation) (no gain) |
| Many `Integer`/`Long` objects in heap | [Primitive arrays](references/allocation.md#primitive-arrays-instead-of-boxed-collections), [primitive accumulators](references/allocation.md#primitive-accumulators) |
| `==` on `Integer`/`Long` | [Integer cache](references/allocation.md#integer-cache-and-boxed-identity) |
| `ArrayList.grow`/`HashMap.resize` in profiles | [Presized ArrayList](references/allocation.md#presized-arraylist), [newHashMap](references/allocation.md#hashmap-newhashmap-sizing) |
| String keys built per lookup | [Record keys](references/allocation.md#records-as-composite-map-keys) |
| Stream pipelines in hot loops | [Streams with collect](references/allocation.md#streams-versus-loops-with-collection), [primitive reductions](references/allocation.md#primitive-stream-reductions) |
| Request to add `final` for speed | [final and CHA](references/codegen.md#final-classes-and-class-hierarchy-analysis) (no gain) |
| Megamorphic interface call site | [Sealed switch](references/codegen.md#pattern-switch-over-a-sealed-hierarchy) |
| Hand-written array compare/copy loops | [Array intrinsics](references/codegen.md#array-intrinsics-in-javautilarrays) |
| Float/double reductions dominate | [Vector API](references/codegen.md#vector-api-for-floating-point-reductions) |
| Fixed pool threads blocked in I/O | [Virtual threads](references/concurrency.md#virtual-threads-for-blocking-tasks) |
| `jdk.VirtualThreadPinned` events | [Pinning after JEP 491](references/concurrency.md#virtual-thread-pinning-after-jep-491) |
| `get` then `put` caches, duplicate work | [computeIfAbsent](references/concurrency.md#concurrenthashmap-computeifabsent) |
| Contended `AtomicLong` statistics | [LongAdder](references/concurrency.md#longadder-for-contended-counters) |
| Pause goals, collector choice | [G1](references/runtime.md#g1-default-collector), [ZGC](references/runtime.md#generational-zgc), [Parallel](references/runtime.md#parallel-gc-for-throughput) |
| Slow startup or warmup | [AppCDS](references/runtime.md#appcds-dynamic-archive), [AOT cache](references/runtime.md#aot-cache), [AOT profiles](references/runtime.md#aot-method-profiles) |
| Heap full of small objects | [Compact headers](references/runtime.md#compact-object-headers) |
| JNI glue or native call cost | [FFM downcalls](references/runtime.md#ffm-downcalls-instead-of-jni), [critical downcalls](references/runtime.md#critical-ffm-downcalls), [arenas](references/runtime.md#arena-scoped-native-memory) |

## Rules

- Benchmarks use JMH with forks, warmup, `@State` inputs built in
  `@Setup(Level.Trial)`, and every result returned or consumed by a
  `Blackhole`. Never time a loop with `System.nanoTime` in `main`.
- Pass shared JVM options to JMH with `-jvmArgs`, not `-jvmArgsAppend`,
  and read each `# VM options:` line: command-line options replace
  annotation values.
- One construct per measured change, so each result is attributable. A
  candidate that does less work (skipped validation, cached result,
  smaller input) is invalid.
- Never trade semantics for speed: keep exception types, `null` handling,
  iteration order, floating-point results (unless the contract allows
  reassociation and the oracle uses a tolerance), and memory-model
  guarantees (`volatile`, locks, safe publication).
- Process-wide flags (collector, heap, compact headers, AOT cache, native
  access) need an application-level measurement and a stated deployment
  consequence. Match training and production JDK, OS, architecture, and
  class path for CDS/AOT caches.
- `jdk.tracePinnedThreads` was removed in JDK 24; use the
  `jdk.VirtualThreadPinned` JFR event.
- JMH refuses to start while another run holds `jmh.lock` in
  `java.io.tmpdir`. Do not pass `-Djmh.ignoreLock=true` on a dedicated
  benchmark host; on a shared machine give the run a private
  `-Djava.io.tmpdir` and label its timings as shared-machine results.
- The cards' async-profiler, `perf`/`perfasm`, and `hsdis` commands were
  never executed; treat them as unverified.

## Bundled tools

- `assets/examples/verify.sh verify|benchmark|measure|tools|startup`: builds
  the Maven/JMH catalog and the JNI/FFM library in a temp copy. `verify`
  runs every oracle; `benchmark` runs each benchmark once; `measure` runs
  JMH `-prof gc`, exports JSON, and asserts the allocation claims; `tools`
  exercises GC logs, JFR, jcmd, JIT logs, and pinning events; `startup`
  builds AppCDS and AOT caches and times them with hyperfine. Needs JDK 25,
  Maven, a C compiler (`CC`), and python3.
- `scripts/jmh_compare.py`: prints JMH JSON rows with `gc.alloc.rate.norm`,
  asserts allocation pairs, or compares two runs by row identity; exits 1
  on a failed check and 2 on invalid input.
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): JMH anatomy and pitfalls,
  `-prof gc`, JSON comparison, JFR, jcmd, async-profiler, GC and JIT logs.
- [Allocation](references/allocation.md): escape analysis, strings,
  boxing, presizing, record keys, streams.
- [Code generation](references/codegen.md): `final`/CHA, sealed switch,
  array intrinsics, Vector API.
- [Concurrency](references/concurrency.md): virtual threads, pinning,
  `computeIfAbsent`, `LongAdder`.
- [Runtime and interop](references/runtime.md): G1, ZGC, Parallel,
  AppCDS, AOT cache and profiles, compact headers, FFM.

## Completion evidence

The final report contains:

- JDK vendor and version, `--release`, JVM flags, collector, OS/CPU;
- the JFR view, log excerpt, or JMH row that attributed the cost;
- the construct applied, with its **Use when** conditions checked;
- the oracle command and result, including edge and error cases;
- baseline and candidate JMH rows with units, error, and
  `gc.alloc.rate.norm` from the same machine and flags, plus the
  application-level result;
- anything not run (other JDKs, Linux-only profilers, production load)
  stated as not verified.
