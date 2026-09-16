# Java performance

Record JDK/vendor/version, JVM options, heap/collector, container CPU/memory
limits, classpath, and workload. Use JMH for isolated JVM microbenchmarks and
JFR or the project's production profiler for application attribution.
Compilation warmup, fork isolation, constant folding, and dead-code elimination
can dominate naive loop timing.

Benchmark the intended operation, consume results using the harness, and do not
put all data in compile-time constants. Separate startup, warmed execution,
throughput, and latency. Keep benchmark state and setup at the correct scope;
moving allocation out of the timed operation changes the question when callers
pay that cost in practice.

Investigate allocation rate, object retention, cache locality, synchronization,
and I/O before replacing language constructs. Autoboxing and streams can matter,
but the JIT may inline, eliminate, or scalar-replace work. Check evidence before
introducing primitive collections or hand-written loops, and include their
representation and API costs.

Measure lock contention and scheduling directly. Virtual threads can improve
concurrency for appropriate blocking workloads; they do not accelerate CPU-bound
work by themselves. Verify the selected JDK's behavior rather than applying old
pinning or synchronization assumptions universally.

For collector or heap changes, compare pause distributions, throughput, memory
limits, and failure behavior under the same workload. A smaller allocation count
does not by itself prove a better latency distribution. Keep native memory and
direct-buffer lifetime separate from Java heap accounting.

Sources: [OpenJDK JMH][ref-openjdk-jmh], [JDK Mission
Control][ref-jdk-mission-control], [JDK Flight Recorder][jdk-flight-recorder].

## Executable fixtures

Requires a JDK supporting --release 8 and POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in [the java
assets](../assets/examples). Copy that directory intact when adapting a fixture.
Run only the selected language, not all toolchains.

### Semantic regression cases

Source: [Semantics.java][ref-semantics-java].

| Case | Required contract |
| --- | --- |
| 1 | String value versus reference identity |
| 2 | Immutable map-key snapshot |
| 3 | Floating-point regrouping |
| 4 | Restoring thread interrupt status |
| 5 | Atomic read-modify-write |
| 6 | Callbacks outside a monitor |
| 7 | Canonical ordering |
| 8 | Locale-independent normalization |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The [shared contract](executable-fixtures.md) explains
input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Copy [the java asset directory](../assets/examples) intact. Run the following
commands in its `benchmarks/` subdirectory.

Provision Maven and a compatible JDK, then:

```sh
mvn package
java -jar target/benchmarks.jar 'example.DelimiterBench.*' \
  -rf json -rff results.json
```

The native project pins JMH 1.37 and explicit compiler/shade plugin versions; it
needs dependency resolution and was not built in this offline environment. Use
the same JDK and JVM flags for matched runs. JMH retains its full native CLI;
change forks, warmups, measurement duration and profilers deliberately. The
illustrative annotation counts are starting settings, not proof of stability.

The returned count is consumed by JMH. Setup generates input and checks an
independent expected count outside measurement. `split(":", -1)` preserves
trailing empty segments; the default split limit would break equivalence.
Measure GC/allocation in a separate or explicitly instrumented run. Do not time
only `System.nanoTime()` around one call or include compilation in a hot-loop
claim. Kotlin/Scala JVM projects should invoke their actual compiled code from
the project's JMH integration rather than benchmarking a Java translation.

Sources: [source][source] and [source][source-2]

## Failure reproduction

Source: [the isolated reproducer](../assets/examples/reproduction). From the
skill root, run `sh assets/examples/verify.sh reproduction`. Direct commands
below assume a clean copy of the reproduction directory.

Expected: equal numeric values compare equal.

Actual: reference identity for separately boxed `1000` values is false. The
verifier copies, compiles, and runs this source in a temporary directory.

[jdk-flight-recorder]: https://docs.oracle.com/en/java/javase/25/jfapi/flight-recorder.html
[source]: https://github.com/openjdk/jmh
[source-2]: https://github.com/openjdk/jmh/tree/master/jmh-samples

[ref-openjdk-jmh]: https://openjdk.org/projects/code-tools/jmh/
[ref-jdk-mission-control]: https://openjdk.org/projects/jmc/
[ref-the-fixture-execution-contract]: executable-fixtures.md
[ref-semantics-java]: ../assets/examples/correctness/Semantics.java
