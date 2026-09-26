---
name: optimize-kotlin-code
description: >-
  Profiles and optimizes Kotlin/JVM CPU time, allocations, and coroutine
  latency with JMH, JFR, and bytecode checks. Use when a Kotlin benchmark or
  profile shows the cost. Not for Kotlin/Native or Kotlin/JS.
---

# Optimize Kotlin Code

Make a measured Kotlin hot path cheaper without changing observable
behavior. Each change applies one reference card to a cost that a profile
attributes, is checked by an equivalence oracle, and is kept only if the
evidence the card names improves: a `javap` instruction pattern, bytes per
call, `gc.alloc.rate.norm`, a JMH score, or exact virtual time. Several
cards record "no difference" for common Kotlin rules because C2 escape
analysis already removes the cost, so read the card before applying a
construct.

## Workflow

1. Record the target: `kotlinc -version` or the Kotlin Gradle/Maven plugin
   version, `jvmTarget`, compiler arguments (`-Xlambdas`,
   `-Xstring-concat`, opt-ins), `java -version`, JVM flags, and the
   kotlinx.coroutines version. Identify the backend; JVM evidence does not
   transfer to Kotlin/Native or Kotlin/JS ([backend boundary][boundary]).
1. Reproduce the workload on the deployed JDK and flags. Pick the metric:
   time per operation, throughput, tail latency, bytes per operation, GC
   count, thread count, or wall time of a coroutine pipeline.
1. Attribute the cost before editing:
   - unknown hot spot: a JFR recording, then `jfr view
     allocation-by-class` and `cpu-time-hot-methods`
     ([JFR](references/measurement.md#jfr-allocation-profile));
   - suspected compile-time cost (lambda objects, boxing, range objects):
     `javap -c -p` on the built class
     ([javap](references/measurement.md#javap-bytecode-inspection));
   - one function: a JMH benchmark with `-prof gc`
     ([JMH](references/measurement.md#jmh-through-maven-for-kotlin));
   - coroutine waiting: `runTest` virtual time
     ([virtual time](references/measurement.md#virtual-time-with-runtest)).
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: baseline and candidate on the same inputs,
   including empty, one element, boundary values (`Int.MIN_VALUE`,
   values outside the `Integer` cache), non-ASCII strings, exceptions,
   and cancellation. `assets/examples/constructs/` shows the shape.
1. Apply the change.
1. Verify with the card's **Verify** steps: behavior first, then the
   named evidence. Allocation assertions run after warm-up with `-Xbatch`;
   run the escape-analysis control
   ([noea](references/measurement.md#escape-analysis-control-run)) when a
   bytecode change shows no allocation difference.
1. Measure baseline and candidate with the same JDK, flags, input, and
   machine; keep the change only if the metric moved beyond the JMH error
   and the application workload also improved.
1. Report with [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| `invokedynamic` Function objects, `Function1.invoke` in hot callees | [inline](references/inline.md#inline-higher-order-function) |
| `Ref` boxes (`IntRef`, `ObjectRef`) in `javap` | [captured var](references/inline.md#captured-var-in-a-non-inline-lambda) |
| `Class<T>` parameters used only for `isInstance` or casts | [reified](references/inline.md#reified-type-parameter) |
| One stored lambda keeps a function non-inline | [noinline](references/inline.md#noinline-parameter) |
| Inline function wraps its lambda in a `Runnable` or object | [crossinline](references/inline.md#crossinline-parameter) |
| Wrapper class per value (IDs, money, units) | [value class](references/representation.md#value-class-used-as-its-own-type) |
| `box-impl` calls, `List` of value classes | [value class boxing](references/representation.md#value-class-boxing-at-generic-nullable-and-interface-boundaries) |
| `Integer.valueOf` / `intValue` in bulk numeric code | [primitive arrays](references/representation.md#primitive-arrays-instead-of-list-of-int-and-array-of-int), [non-null locals](references/representation.md#non-null-primitive-locals-instead-of-int) |
| Getter calls for constants | [const val](references/representation.md#const-val-instead-of-val) |
| Java callers of properties or companion functions | [JvmField](references/representation.md#jvmfield-on-properties-read-by-java-or-across-classes), [JvmStatic](references/representation.md#jvmstatic-on-companion-functions) |
| `copy(...)` per element in a loop | [local accumulators](references/representation.md#local-accumulators-instead-of-data-class-copy-in-a-loop) |
| Data class `equals` hot on keys sharing a long first property | [equals order](references/representation.md#explicit-equals-order-for-hot-keys) |
| `filter`/`map` chains ending in `take`/`first` | [Sequence](references/collections.md#sequence-for-a-multi-step-chain-that-stops-early) |
| Sequence-vs-Iterable claims for short full chains | [short chains](references/collections.md#sequence-versus-iterable-for-short-chains) |
| Same `Sequence` consumed twice | [materialize](references/collections.md#materialize-a-sequence-that-is-consumed-more-than-once) |
| `map { }.sum()`, `groupBy { }.mapValues`, `associate { it to }` | [sumOf](references/collections.md#sumof-instead-of-map-then-sum), [groupingBy](references/collections.md#groupingby-eachcount-instead-of-groupby-mapvalues), [associateWith](references/collections.md#associatewith-instead-of-associate-with-pair) |
| `list = list + x` or `s += ...` in loops | [buildList](references/collections.md#buildlist-with-capacity-instead-of-list-plus-element), [buildString](references/collections.md#buildstring-instead-of-string--in-a-loop) |
| Proposal to hand-roll `StringBuilder` for one template | [templates](references/collections.md#string-templates) |
| `IntRange`/`IntProgression` allocations in loops | [counted loops](references/control-flow.md#range-loops-the-compiler-lowers-to-counted-loops), [range objects](references/control-flow.md#range-objects-from-step-reversed-and-foreach) |
| Rewriting `when` for speed | [sealed](references/control-flow.md#when-over-sealed-types), [enum](references/control-flow.md#when-over-enum-entries), [String](references/control-flow.md#when-over-string-constants) |
| `by lazy` on many instances, lock contention on first access | [SYNCHRONIZED](references/control-flow.md#lazy-with-synchronized-default), [PUBLICATION](references/control-flow.md#lazy-with-publication), [NONE](references/control-flow.md#lazy-with-none), [eager val](references/control-flow.md#eager-val-instead-of-lazy) |
| Blocking calls on `Dispatchers.Default` | [Dispatchers.IO](references/coroutines.md#dispatchersio-for-blocking-calls), [limitedParallelism](references/coroutines.md#limitedparallelism-for-a-bounded-resource) |
| `GlobalScope`, work continuing after cancel | [structured concurrency](references/coroutines.md#structured-concurrency-instead-of-globalscope) |
| Sequential independent suspend calls | [async/awaitAll](references/coroutines.md#async-and-awaitall-for-independent-calls) |
| `runBlocking` per request or inside suspend code | [no runBlocking](references/coroutines.md#suspend-calls-instead-of-runblocking-in-hot-paths) |
| Slow Flow producer and collector, stale values, heavy upstream | [buffer](references/coroutines.md#flow-buffer), [conflate](references/coroutines.md#flow-conflate), [flowOn](references/coroutines.md#flowon-for-upstream-context) |
| Shared state across coroutines | [Mutex](references/coroutines.md#mutex-for-critical-sections-that-suspend), [atomics](references/coroutines.md#atomics-or-synchronized-for-critical-sections-that-do-not-suspend) |
| Producer blocked on channel hand-off | [Channel capacity](references/coroutines.md#channel-capacity) |
| `catch (e: Exception)` around suspend calls, CPU loops ignoring cancel | [rethrow](references/coroutines.md#rethrow-cancellationexception), [ensureActive](references/coroutines.md#ensureactive-in-cpu-bound-loops) |

## Rules

- Measure the deployed configuration: same JDK, JVM flags, `jvmTarget`,
  and compiler arguments for baseline and candidate. Never measure under
  `-Xint`, a debugger, or a coverage agent.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric did not move; several cards record "no
  difference" (inline and captured `var` allocations, `associateWith`)
  because C2 already removed the cost.
- A candidate that does less work is invalid: a lazy chain that skips
  side effects the caller needed, `conflate` dropping events that must be
  processed, a buffer that lets the producer run past a contract, or
  swallowed cancellation.
- Preserve semantics the rewrite can change: evaluation order and count
  of lambdas (eager vs lazy), exception timing, duplicate and key order
  in maps, `Int` overflow in `sumOf`, value-class identity and Java
  names, `lazy` initializer run count, and cancellation propagation.
- JMH benchmark classes must be `open`; return or consume every result.
  Do not ignore the JMH lock for results you report; say so if you did.
- Allocation claims need the thread counter or `gc.alloc.rate.norm`,
  not bytecode alone; bytecode claims need `javap` from the project's own
  compiler version.
- Report only numbers you measured (with JDK, Kotlin, and machine) or
  numbers from a linked primary source.

## Bundled tools

`assets/examples/verify.sh` copies `assets/examples/constructs/` (Maven:
Kotlin 2.4.20, kotlinx.coroutines 1.11.0, JMH 1.37) to a temporary
directory and builds there:

- `verify [GROUP...]` (default): equivalence and allocation oracles for
  every card; groups `inline`, `representation`, `collections`,
  `control`, `coroutines`.
- `noea`: the same with escape analysis off, allocation lines as `INFO`.
- `bytecode`: `javap` assertions for every bytecode claim.
- `benchmark`: JMH smoke, each benchmark once, no timing.
- `measure`: JMH with `-prof gc`; `BENCH_FILTER` selects benchmarks and
  the JSON result is kept only when `BENCH_OUT` names a directory.
- `jfr`: JFR recording of the collection oracles and its allocation view.

## References

- [Measurement](references/measurement.md): javap, allocation counter,
  escape-analysis control, JMH via Maven, gc profiler, virtual time, JFR,
  kotlinx-benchmark, backend boundary.
- [Inline functions and lambdas](references/inline.md): inline,
  captured var, reified, noinline, crossinline.
- [Data representation](references/representation.md): value classes,
  primitive arrays, nullable primitives, const, JvmField, JvmStatic,
  data classes.
- [Collections and strings](references/collections.md): sequences,
  sumOf, buildList, buildString, templates, groupingBy, associateWith.
- [Loops, when, and lazy](references/control-flow.md): range lowering,
  `when` lowering, lazy modes.
- [Coroutines](references/coroutines.md): dispatchers, structured
  concurrency, runBlocking, Flow, Mutex, channels, cancellation.

## Completion evidence

The final report contains:

- Kotlin compiler version, `jvmTarget`, compiler arguments, JDK and JVM
  flags, kotlinx.coroutines version, OS and CPU;
- the profile, `javap` output, or counter that attributed the cost;
- the card applied and its preconditions checked;
- the oracle command and result, including edge, exception, and
  cancellation cases;
- baseline and candidate numbers from the same JDK and machine, with
  units and JMH error or exact byte and virtual-time values, plus the
  application-level result;
- every check not run (other backends, Gradle-only harnesses, production
  load) stated as not verified.

[boundary]: references/measurement.md#kotlinnative-and-kotlinjs-boundary
