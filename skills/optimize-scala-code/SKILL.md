---
name: optimize-scala-code
description: >-
  Profiles and optimizes Scala JVM CPU time and allocations with JMH, JFR, and
  javap: collections, boxing, opaque types, inline. Use when a Scala benchmark
  or profile shows the cost. Not for style or migration edits.
---

# Optimize Scala Code

Make a measured Scala hot path cheaper without changing observable
behavior. Each change applies one reference card to a cost that a profile
attributes, is proven equivalent by an oracle, and is kept only if the
metric the card names improves: JMH time, `gc.alloc.rate.norm` B/op, a
ThreadMXBean byte delta, a `javap` instruction, or a call count. The cards
record preconditions and counter-indications, so read the card before
applying a construct. Scala 3 on the JVM is the default; the cards label
Scala 2.13, Scala.js, and Scala Native differences.

## Workflow

1. Record the target: Scala version (`scalaVersion` in `build.sbt` or
   `//> using scala`), backend (JVM, Scala.js, Native), `scalacOptions`,
   `java -version`, JVM flags, and the build tool version
   (`scala-cli version`, `project/build.properties`). Keep the project's
   Scala and JDK versions; do not upgrade them to reach a construct unless
   the user asked.
1. Reproduce the workload on the deployed backend and pick the metric the
   user cares about: ns/op, tail latency, throughput, B/op, live heap, GC
   time, or startup.
1. Attribute the cost before editing
   ([measurement](references/measurement.md)):
   - unknown hotspot: JFR with `-XX:StartFlightRecording`, then
     `jfr view hot-methods` and `jfr view allocation-by-class`;
   - one method: a JMH benchmark run with `-prof gc`;
   - compile-time shape (boxing, switch, lazy val, inline): `javap -c -p`.
1. Choose one construct from the routing table whose **Use when** matches
   the evidence and whose **Do not use when** does not.
1. Write the oracle first: keep the old code as `baseline`, compare it
   with the candidate on empty, boundary, overflow, duplicate, and
   side-effect-count inputs, and add an allocation assertion for allocation
   cards ([semantic oracle][oracle]).
1. Apply the change, then check the bytecode where the card says so.
1. Measure baseline and candidate in the same JMH run
   (`scala-cli --power run --jmh <inputs> -- -prof gc <regex>` or
   `sbt -batch 'bench/Jmh/run -prof gc <regex>'`, then `sbt shutdown`).
   Keep the change only if the target metric's `Score ± Error` intervals
   do not overlap and nothing else regressed.
1. Re-run the application-level workload, then report using
   [the report template](assets/performance-report.md).

## Route evidence to a construct

| Evidence | Card |
| --- | --- |
| `LinearSeqOps.apply` or `List.length` inside an index loop | [Indexed access](references/collections.md#indexed-access-indexedseq-instead-of-listapply), [performance table](references/collections.md#sequence-choice-by-the-performance-table) |
| Heap full of `Integer`/`Long` plus `::` cells | [ArraySeq of Int](references/collections.md#primitive-storage-arrayseq-of-int-instead-of-list-of-int) |
| `:+` on a `List` in a loop | [ListBuffer](references/collections.md#listbuffer-instead-of-repeated-list-append) |
| `filter`/`map` chain ending in a reduction | [Iterator chain](references/collections.md#iterator-chain-instead-of-a-strict-chain) |
| Chain of transformers ending in one collection | [View chain](references/collections.md#view-chain-before-a-single-materialization) |
| `map`/`sum`/`foldLeft` over `Array[Int]` with B/op | [Array while loop](references/collections.md#array-with-a-while-loop-instead-of-map-and-sum) |
| Array or builder regrowth with a known size | [sizeHint](references/collections.md#arraynewbuilder-with-an-exact-sizehint), [ArrayBuffer sizeHint](references/collections.md#arraybuffer-with-sizehint) |
| `ArrayBuffer[Int]` of primitives, boxed `Integer`s | [Array.newBuilder](references/collections.md#arraynewbuilder-instead-of-arraybuffer-for-primitives) |
| `List.updated` or other L operations in a loop | [Performance table](references/collections.md#sequence-choice-by-the-performance-table) |
| String `+` in a fold or loop | [StringBuilder](references/collections.md#stringbuilder-instead-of-string-concatenation-in-a-fold) |
| Immutable `Map` rebuilt per update in a fold | [mutable.HashMap](references/collections.md#mutablehashmap-instead-of-folding-an-immutable-map), [HashMap.merge](references/collections.md#javautilhashmapmerge-for-counting), [slot array](references/collections.md#slot-array-for-counters-keyed-by-a-small-set) |
| `groupBy(...).view.mapValues(...)` | [groupMapReduce](references/collections.md#groupmapreduce-instead-of-groupby-and-mapvalues) |
| `Seq.contains` inside a loop | [Set membership](references/collections.md#set-for-repeated-membership-tests) |
| `Numeric.plus(Object, Object)` boxing | [Primitive overload](references/language.md#primitive-overload-instead-of-a-generic-numeric-method), [inline def](references/language.md#inline-def-for-a-generic-numeric-helper), [@specialized](references/language.md#specialized-scala-213-only) |
| Custom generic function trait on primitives | [Function1 specialization](references/language.md#function1-specialization-instead-of-a-custom-generic-sam) |
| Wrapper type stored in arrays or collections | [Opaque type](references/language.md#opaque-type-instead-of-a-value-class-for-arrays), [value class](references/language.md#value-class-extends-anyval) |
| Log/trace message built while disabled | [Inline parameter](references/language.md#inline-parameter-for-a-disabled-log-message), [by-name](references/language.md#by-name-parameter-for-a-disabled-log-message) |
| `StackOverflowError` from recursion | [@tailrec](references/language.md#tailrec-loop-instead-of-non-tail-recursion) |
| Hot `match` on `Int` literals | [@switch](references/language.md#switch-on-an-int-match), [sealed match](references/language.md#sealed-trait-match) |
| Lazy val read in a hot loop | [Hoist](references/language.md#hoist-a-lazy-val-read-out-of-a-loop), [@threadUnsafe](references/language.md#threadunsafe-lazy-val) |
| `implicit class` wrapper allocations | [Extension method](references/language.md#extension-method-instead-of-an-implicit-class), [AnyVal implicit class](references/language.md#implicit-class-extending-anyval) |
| `Array` passed as `Seq[Int]` | [IArray](references/language.md#iarray-instead-of-a-seq-view-of-an-array) |
| `f"..."` on plain values in hot code | [s interpolator](references/language.md#s-interpolator-instead-of-f-for-plain-values) |
| Futures on `global` stall, blocking calls | [global](references/concurrency.md#executioncontextglobal-for-cpu-bound-futures), [blocking](references/concurrency.md#blocking-inside-executioncontextglobal), [dedicated pool](references/concurrency.md#dedicated-executioncontext-for-blocking-io) |
| Trivial `map` callbacks hop threads | [parasitic](references/concurrency.md#executioncontextparasitic-for-cheap-callbacks) |
| Large pure CPU-bound collection work, idle cores | [.par](references/concurrency.md#parallel-collections-with-par) |

## Rules

- Same machine, JDK, Scala version, compiler options, JVM flags, and
  inputs for baseline and candidate; run them in one JMH invocation with
  at least 2 forks. A 1-fork, 1-iteration smoke run is not a result.
- One construct per measured change, so each result is attributable.
  Revert a change whose metric does not move; several cards record
  measured "no difference" or "worse" results.
- A candidate that does less work (skipped validation, cached result,
  smaller input, dead result) is invalid. Build inputs in `@Setup` and
  return every result from `@Benchmark` methods.
- Preserve the observable contract: results, exceptions and their timing,
  overflow, ordering, duplicates, laziness and side-effect counts, single
  traversal of iterators, thread and execution-context behavior.
- Bytecode shows what the compiler emitted, not what C2 runs: pair every
  `javap` claim with an allocation or timing measurement on warmed code.
- Never claim JVM results for Scala.js or Scala Native; measure those
  backends with their own tools and say so when you cannot.
- `scala-cli --jmh` needs `--power` and the Bloop server (no
  `--server=false`); give each JMH run its own `java.io.tmpdir` on a
  shared machine.

## Bundled tools

- `assets/examples/verify.sh MODE` (needs scala-cli 1.10+ and a JDK 17+)
  copies the examples to a temp directory and runs there, so no
  `.scala-build/`, `.bsp/`, or class files land in the skill. Modes:
  `verify` (equivalence and allocation oracles), `diagnostics` (javap
  assertions, Scala 2.13 `@specialized`, expected compile failures),
  `benchmark` (every JMH benchmark once, smoke only), `measure` (JMH with
  `-prof gc`, JSON to `BENCH_OUT`), `profile` (JFR plus `jfr view`), `sbt`
  (sbt 2 with sbt-jmh, smoke).
- `assets/performance-report.md`: the report skeleton.

## References

- [Measurement](references/measurement.md): JMH through scala-cli,
  `-prof gc`, sbt-jmh, ThreadMXBean oracle, javap, JFR, semantic oracle.
- [Collections](references/collections.md): performance table, indexed
  access, primitive storage, ArrayBuffer, builders, iterators, views,
  arrays, strings, maps, grouping, membership.
- [Language](references/language.md): boxing, inline, `@specialized`,
  function specialization, opaque and value classes, by-name,
  `@tailrec`, `@switch`, sealed matches, lazy vals, extensions, `IArray`,
  interpolators.
- [Concurrency](references/concurrency.md): `global`, `blocking`,
  dedicated pools, `parasitic`, parallel collections.

## Completion evidence

The final report contains:

- Scala version, backend, JDK, build tool, CPU/OS, compiler options, and
  JVM flags;
- the profile or benchmark output that attributed the cost;
- the construct applied, with its **Use when** conditions checked;
- the oracle command and result, including edge cases;
- JMH output for baseline and candidate with `Score ± Error`, forks, and
  `gc.alloc.rate.norm`, plus the application-level result;
- bytecode evidence where the card names it;
- anything not run (other backends, JDKs, Scala versions, production
  profiles) stated as not verified.

[oracle]: references/measurement.md#semantic-oracle-for-collection-rewrites
