# JVM performance gotchas (Java, Kotlin, Scala)

Read this with the language reference when the cost is JIT warmup, GC, or the JMH harness.

## JMH

- Mistake: a hand-written `System.nanoTime` loop. Fix: JMH. The JIT compiles in tiers and inlines
  based on observed profiles, so a loop without forks and warmup measures interpreter and compile
  time.
- Mistake: a `@Benchmark` method that computes and discards. Fix: return the value or pass it to a
  `Blackhole`. Dead-code elimination removes the work otherwise.
- Mistake: constant inputs as `final` fields or literals. Fix: read inputs from non-final `@State`
  fields, since constant folding removes the work; create them in `@Setup`.
- Mistake: `@Fork(0)` or one fork. Fix: use at least 3 forks for results you report, because profile
  pollution and JIT luck vary by JVM instance. Compare the score with its error (`±`) and do not
  report a difference inside it.
- Mistake: loops inside `@Benchmark` to get more work per call. Fix: let JMH loop; if you must, know
  JIT can unroll and hoist across iterations (`@OperationsPerInvocation` must match the loop count).
- Mistake: reading only `avgt`. Fix: add `-prof gc` and read `gc.alloc.rate.norm` (bytes per
  operation), which is deterministic and catches allocation regressions timings hide; `-prof stack`
  for hot frames, `-prof perfasm` on Linux for assembly.
- Mistake: benchmarking a stateful structure that grows across iterations. Fix: reset in
  `@Setup(Level.Invocation)` only for slow operations; its timer overhead swamps micro operations.
  Prefer `Level.Iteration` and size the structure to stay steady.
- Mistake: benchmarking with a different `-Xmx`, GC, or JDK than production. Fix: pass the
  production flags via `-jvmArgs` and record `java -version`.

## JIT and warmup

- Mistake: concluding from a run that mixes interpreter, C1, and C2 phases. Fix: check
  `-XX:+PrintCompilation` and let the benchmark reach steady state; for startup complaints measure
  cold runs separately and consider AppCDS or CRaC rather than code changes.
- Mistake: assuming a method inlines. Fix: `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` shows
  `too big`, `hot method too big`, or `callee is too large`; the default limits are
  `MaxInlineSize=35` bytecode bytes for cold and `FreqInlineSize=325` for hot methods. Splitting a
  large method so its hot part fits can help more than any flag.
- Mistake: megamorphic call sites treated as inlinable. Fix: a call site that sees three or more
  receiver types is an indirect call. Reduce the receiver types on the hot path or use a `switch`
  over a tag.
- Mistake: lambdas or streams on the hot path assumed free. Fix: they allocate when capturing and
  stream pipelines have fixed setup cost; use them unless a profile shows it. Non-capturing lambdas
  are cached.
- Mistake: trusting escape analysis to remove allocations it cannot prove. Fix: confirm with
  `-prof gc` (`alloc.rate.norm` drops to 0) rather than assuming; escape analysis fails across
  non-inlined calls and megamorphic sites.
- Mistake: safepoint bias in sampling profilers. Fix: use JFR, or async- profiler on Linux/macOS,
  which do not sample only at safepoints.

## GC

- Mistake: tuning GC flags before reading a GC log. Fix: `-Xlog:gc*:file=gc.log` and read pause
  times, allocation rate, and promotion; the usual fix is to allocate less, not to change
  collectors.
- Mistake: changing `-Xmx` without `-Xms`, or setting heap above the container limit. Fix: the JVM
  is container-aware; by default it uses 25% of container memory as max heap, so set
  `-XX:MaxRAMPercentage` or `-Xmx` deliberately, leaving room for metaspace, thread stacks, and
  direct buffers.
- Mistake: comparing collectors on a short benchmark. Fix: run the application-level workload for
  long enough to see promotion and mixed collections; G1, ZGC, Shenandoah, and Parallel trade
  throughput for pause time, so pick from the latency or throughput goal.
- Mistake: object pools for short-lived objects. Fix: young-generation allocation is cheap; pooling
  raises old-generation retention and synchronization cost. Pool only expensive objects, such as
  large buffers or connections.

## JFR

- Mistake: profiling with heavy instrumentation. Fix:
  `java -XX:StartFlightRecording=duration=60s,filename=rec.jfr,settings=profile` has low overhead;
  view hot methods and allocation by class with
  `jfr print --events jdk.ExecutionSample,jdk.ObjectAllocationSample rec.jfr` or JDK Mission
  Control. Allocation events are sampled, so compare shares, not exact counts.
