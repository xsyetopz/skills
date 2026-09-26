# Collection constructs

Each card replaces a collection shape that a profile blames for cost.
Baselines and candidates are in
`assets/examples/constructs/Collections.scala`; `CollectionChecks` proves
equivalence and the allocation claim, and `bench/Benchmarks.scala` holds
the JMH pairs.

Tier: executed locally (`verify.sh verify`, `benchmark`, `measure`).
Measured on: Apple M1 Max, macOS arm64, OpenJDK 25.0.4.1, Scala 3.8.4
(standard library `scala-library` 3.8.4), scala-cli 1.16.0. B/op values
come from the ThreadMXBean oracle after 20,000 warm-up calls and are
deterministic for this toolchain and input. Timings come from JMH
(2 forks, 5 x 1 s warmup, 5 x 1 s measurement) on a machine shared with
other builds; they show direction, not portable speedups.

## Contents

- Sequence choice by the performance table
- Indexed access: IndexedSeq instead of List.apply
- Primitive storage: ArraySeq of Int instead of List of Int
- ListBuffer instead of repeated List append
- Iterator chain instead of a strict chain
- View chain before a single materialization
- Array with a while loop instead of map and sum
- ArrayBuffer with sizeHint
- Array.newBuilder instead of ArrayBuffer for primitives
- Array.newBuilder with an exact sizeHint
- StringBuilder instead of string concatenation in a fold
- mutable.HashMap instead of folding an immutable Map
- java.util.HashMap.merge for counting
- Slot array for counters keyed by a small set
- groupMapReduce instead of groupBy and mapValues
- Set for repeated membership tests

## Sequence choice by the performance table

**Definition.** The Scala collections overview lists the complexity of
each operation per collection type ([performance characteristics][perf]):
C constant, eC effectively constant, aC amortized constant, Log
logarithmic, L linear, `-` unsupported.

| Type | head | tail | apply | update | prepend | append | insert |
| --- | --- | --- | --- | --- | --- | --- | --- |
| List | C | C | L | L | C | L | - |
| LazyList | C | C | L | L | C | L | - |
| ArraySeq | C | L | C | L | L | L | - |
| Vector | eC | eC | eC | eC | eC | eC | - |
| Queue | aC | aC | L | L | C | C | - |
| Range | C | C | C | - | - | - | - |
| String | C | L | C | L | L | L | - |
| ArrayBuffer | C | L | C | C | L | aC | L |
| ListBuffer | C | L | L | L | C | C | L |
| StringBuilder | C | L | C | C | L | aC | L |
| Array | C | L | C | C | - | - | - |

Sets and maps: `HashSet`/`HashMap` (immutable and mutable) lookup, add,
and remove are eC; `TreeSet`/`TreeMap` are Log.

**Use when.**

- A profile shows `LinearSeqOps.apply`, `List.length`, `:+`, or
  `updated` on a `List` inside a loop.
- A new hot data path needs a sequence type.

**Do not use when.**

- The code only traverses front to back and prepends: `List` is already
  C for those, and switching adds conversion cost.
- The type is part of a public API or a pattern-matched ADT (`::`,
  `Nil`): changing it breaks callers. Convert once at the boundary.

**Example.** The `update` column: `List.updated` is L, `Vector.updated`
is eC.

```scala
def baseline(xs: List[Int], i: Int): List[Int] =
  xs.updated(i, -1) // L: copies the i cells before index i

def candidate(xs: Vector[Int], i: Int): Vector[Int] =
  xs.updated(i, -1) // eC: copies one path of the vector's tree
```

Runnable: `UpdateAt` in `Collections.scala`. The next cards apply other
rows.

**Cost removed.** Asymptotic work: an L operation inside a loop over the
same collection makes the loop quadratic. Measured, 1,000 elements,
update at index 900: 21,656 B/op for `List` versus 312 B/op for
`Vector`.

**Verify.**

1. Match the profiled operation to its row before choosing a card;
   `PASS update-at` checks equal results.
1. `PASS update-at allocation (...)` (asserts at most 10%), then the
   chosen card's oracle and JMH pair.

## Indexed access: IndexedSeq instead of List.apply

**Definition.** `List.apply(i)` and `List.length` walk the list (L), so
`while i < xs.length do xs(i)` over a `List` is quadratic. `ArraySeq` has
C `apply` and `Vector` eC ([performance characteristics][perf]).

**Use when.**

- An index loop or `xs(i)` runs over a `List`, or over a `Seq` parameter
  whose runtime class is `List` (check `xs.getClass` or a debugger).
- The access pattern cannot be rewritten as one traversal.

**Do not use when.**

- One traversal suffices: iterate (`for x <- xs`, `xs.iterator`) and
  keep the `List`; converting allocates the whole sequence again.
- The collection is converted inside the hot loop: convert once, outside.

**Example.**

```scala
def baseline(xs: List[Int]): Long =
  var sum = 0L
  var i = 0
  while i < xs.length do { sum += xs(i); i += 1 } // O(i) per xs(i)
  sum

def candidate(xs: IndexedSeq[Int]): Long =
  var sum = 0L
  var i = 0
  while i < xs.length do { sum += xs(i); i += 1 } // C or eC per xs(i)
  sum
```

Runnable: `IndexedAccess` in `Collections.scala`; called with
`list.to(ArraySeq)` and `list.toVector`.

**Cost removed.** Quadratic traversal. JMH, 1,000 elements:
`indexedList` 22,715,947 ± 12,779,953 ns/op; `indexedArraySeq`
1,578 ± 699 ns/op; `indexedVector` 3,614 ± 3,590 ns/op (a second 3-fork
run: 2,578 ± 2,905 and 2,303 ± 1,634 ns/op, so ArraySeq versus Vector is
not resolved here).

**Verify.**

1. `sh assets/examples/verify.sh verify`: `PASS indexed-access`,
   `PASS indexed-access-vector`, `PASS indexed-access-empty`.
1. `BENCH_FILTER='Pairs.indexed' sh assets/examples/verify.sh measure`.

## Primitive storage: ArraySeq of Int instead of List of Int

**Definition.** `immutable.ArraySeq.tabulate[Int]` builds an
`ArraySeq.ofInt` over an `Array[Int]` (one object plus a primitive
array), while `List[Int]` stores one cons cell and, outside the
`Integer` cache (-128 to 127, [Integer.valueOf][integer-cache]), one
boxed `Integer` per element ([ArraySeq][arrayseq]).

**Use when.**

- A long-lived immutable sequence of primitives dominates the heap, or
  `allocation-by-class` shows `Integer`/`Long` plus `::`.
- The consumer needs `apply` or `length` (C on `ArraySeq`).

**Do not use when.**

- The code prepends or takes `tail` repeatedly: those are L on
  `ArraySeq` and C on `List`.
- The element type is a type parameter at construction without a
  `ClassTag`: the factory falls back to a reference array and boxes.

**Example.**

```scala
def baseline(n: Int): List[Int] = List.tabulate(n)(i => i * 1000)
def candidate(n: Int): ArraySeq[Int] =
  ArraySeq.tabulate(n)(i => i * 1000) // ArraySeq.ofInt over Array[Int]
```

Runnable: `Footprint` in `Collections.scala`.

**Cost removed.** Measured, 1,000 elements: 40,016 B/op for the `List`
versus 4,032 B/op for `ArraySeq` (oracle asserts at most 25%).

**Verify.**

1. `PASS footprint` (element-wise equality of both results).
1. `PASS footprint allocation (baseline 40016.0 B/op, candidate
   4032.0 B/op)`.

## ListBuffer instead of repeated List append

**Definition.** `list :+ x` copies the whole list (append is L), so
appending n elements one at a time is quadratic in time and allocation.
`ListBuffer` appends in C and `toList` hands over its cells without
copying: it sets an `aliased` flag and copies only if the buffer is
mutated afterwards ([performance characteristics][perf],
[ListBuffer source][listbuffer]).

**Use when.**

- A loop builds a `List` with `:+` or `++ List(x)`.
- The result must stay a `List` for callers.

**Do not use when.**

- Prepending with `::` and reversing once is simpler and already linear.
- The buffer escapes or is shared between threads: `ListBuffer` is
  mutable and not thread-safe.
- The buffer is modified after `toList`: `ListBuffer` then copies to
  keep the returned list immutable.

**Example.**

```scala
def baseline(xs: List[Int]): List[Int] =
  var out = List.empty[Int]
  for x <- xs do out = out :+ x // copies `out` every time
  out

def candidate(xs: List[Int]): List[Int] =
  val out = mutable.ListBuffer.empty[Int]
  for x <- xs do out += x
  out.toList
```

Runnable: `ListAppend` in `Collections.scala`.

**Cost removed.** Measured, 200 elements: 495,168 B/op versus
7,984 B/op (oracle asserts at most 5%).

**Verify.**

1. `PASS list-append` and `PASS list-append-empty`.
1. `PASS list-append allocation (...)`.

## Iterator chain instead of a strict chain

**Definition.** Each strict transformer (`filter`, `map`) on a `List`
builds a complete intermediate `List`. The same chain on `xs.iterator`
builds only iterator objects and evaluates one element at a time when a
terminal operation (`length`, `sum`, `foldLeft`, `to`) pulls
([iterators][iterators]).

**Use when.**

- A chain of two or more transformers ends in a reduction or one
  materialization, and the intermediates are not reused.

**Do not use when.**

- The iterator is traversed twice: the second traversal sees nothing
  (asserted by `PASS iterator is one-shot`).
- The functions have side effects whose order across stages matters:
  strict chains run all of `filter` before any `map`; iterators
  interleave them per element.
- The terminal is a generic reduction over primitives (`sum`,
  `foldLeft[Long]`): the iterator still boxes each element; see
  [Array with a while loop](#array-with-a-while-loop-instead-of-map-and-sum).

**Example.**

```scala
def baseline(xs: List[Int]): Int =
  xs.filter(_ % 3 == 0).map(_ * 2).length

def candidate(xs: List[Int]): Int =
  xs.iterator.filter(_ % 3 == 0).map(_ * 2).length
```

Runnable: `StrictChain` in `Collections.scala`.

**Cost removed.** Measured, 2,000 elements: 42,664 B/op versus 72 B/op
(iterator objects only). JMH time, 1,000 elements: run 1
`strictChain` 7,854 ± 1,541 and `iteratorChain` 8,063 ± 5,108 ns/op;
run 2 7,565 ± 538 and 45,528 ± 52,523 ns/op. No time benefit was
established: apply this card for allocation or GC pressure and measure
time on your workload.

**Verify.**

1. `PASS strict-chain`.
1. `PASS strict-chain allocation (...)`; `javap -c` of `StrictChain$`
   shows `Iterator.filter` and `Iterator.map` in the candidate.

## View chain before a single materialization

**Definition.** `xs.view` returns a collection whose transformers are
lazy; `to(Factory)` or `toVector` materializes once. The views overview
states that for small collections "the added overhead of forming and
applying closures in views is often greater than the gain from avoiding
the intermediary data structures" ([views][views]).

**Use when.**

- A chain of transformers ends in one strict collection that is large
  enough for the intermediates to show in `-prof gc`.

**Do not use when.**

- The view is kept and traversed more than once: each traversal
  recomputes every stage (asserted by `PASS view-reevaluates`: 6 calls
  for two traversals of 3 elements).
- The stages have side effects: the views overview advises restricting
  views to "purely functional code".
- A `take`, `find`, or `exists` short-circuits and the baseline relied
  on every element being processed: eager effects run for every element,
  a view's only as far as needed.

**Example.**

```scala
def baseline(xs: Vector[Int]): Vector[Int] =
  xs.map(_ + 1).filter(_ % 2 == 0).map(_ * 3)

def candidate(xs: Vector[Int]): Vector[Int] =
  xs.view.map(_ + 1).filter(_ % 2 == 0).map(_ * 3).toVector
```

Runnable: `ViewChain` in `Collections.scala`.

**Cost removed.** Measured, 2,000 elements: 92,648 B/op versus
74,104 B/op (20% less; both still box elements). JMH time: run 1
`viewStrict` 9,015 ± 545 and `viewLazy` 19,117 ± 6,912 ns/op (the view
was slower); run 2 58,943 ± 60,009 and 16,746 ± 1,384 ns/op (noisy).
The time effect is not established; the view reduced bytes only.

**Verify.**

1. `PASS view-chain` and `PASS view-reevaluates`.
1. `PASS view-chain allocation (...)` (asserts at most 90%).

## Array with a while loop instead of map and sum

**Definition.** On `Array[Int]`, `map` returns a new `Array[Int]`, and
`sum` is reached through the implicit `wrapIntArray` conversion to
`mutable.ArraySeq.ofInt` and the generic `sum(Numeric)`, implemented as
`reduce(num.plus)` over `Object` ([IterableOnce source][iterableonce]),
which boxes elements and partial sums. A `while` loop over the array
uses `iaload` and an `Int` accumulator with no allocation.

**Use when.**

- A hot loop over `Array[Int]`, `Array[Long]`, or `Array[Double]` uses
  `map`, `sum`, `foldLeft`, or `foreach`, and `-prof gc` shows B/op.

**Do not use when.**

- The loop is not hot: the functional form is clearer.
- Widening the accumulator would change overflow behavior: `Int`
  addition wraps in both forms (asserted by `PASS array-loop-overflow`);
  widen to `Long` only if the contract allows a different result.

**Example.**

```scala
def baseline(xs: Array[Int]): Int = xs.map(_ + 1).sum

def candidate(xs: Array[Int]): Int =
  var sum = 0
  var i = 0
  while i < xs.length do { sum += xs(i) + 1; i += 1 }
  sum
```

Runnable: `ArrayLoop` in `Collections.scala`.

**Cost removed.** Measured, 2,000 elements: 71,984 B/op versus 0 B/op.
JMH, 1,000 elements: `arrayMapSum` 14,292 ± 9,262 ns/op and
35,984 B/op; `arrayWhile` 553 ± 319 ns/op and 0.004 B/op.

**Verify.**

1. `PASS array-loop` and `PASS array-loop-overflow`.
1. `PASS array-loop allocation (...)`; `verify.sh diagnostics` asserts
   the baseline calls `ArraySeq$ofInt.sum:(Lscala/math/Numeric;)`.

## ArrayBuffer with sizeHint

**Definition.** `mutable.ArrayBuffer` appends in amortized constant
(aC) time by growing a
backing `Array[AnyRef]`; `sizeHint(n)` calls `ensureSize(n)` when n
exceeds the current length, so adding at most n elements causes no
growth copies
([performance characteristics][perf], [ArrayBuffer][arraybuffer],
[ArrayBuffer source][arraybuffer-src]).

**Use when.**

- The element count is known or bounded before the loop, and the buffer
  must stay an `ArrayBuffer` (callers remove, insert, or keep
  appending).

**Do not use when.**

- Elements are primitives and the result can be an array: the buffer
  still boxes each `Int` (next card).
- The bound is a large overestimate: the unused capacity stays allocated
  for the buffer's lifetime.

**Example.**

```scala
def candidate(n: Int): mutable.ArrayBuffer[Int] =
  val b = mutable.ArrayBuffer.empty[Int]
  b.sizeHint(n) // capacity n before the first append
  var i = 0
  while i < n do { b += i * 1000; i += 1 }
  b
```

Runnable: `BufferGrowth` in `Collections.scala`.

**Cost removed.** Growth copies. Measured, 1,000 elements outside the
`Integer` cache: 24,248 B/op (empty buffer) versus 20,104 B/op
(presized); the remaining 16,000 B/op are the boxed `Integer`s.

**Verify.**

1. `PASS buffer-presized`.
1. `PASS buffer-presized allocation (...)` (asserts at most 95%).

## Array.newBuilder instead of ArrayBuffer for primitives

**Definition.** `ArrayBuffer[Int]` stores elements in an
`Array[AnyRef]`, so each `Int` outside the `Integer` cache is boxed.
`Array.newBuilder[Int]` returns `ArrayBuilder.ofInt`, backed by an
`int[]` ([ArrayBuilder source][arraybuilder]).

**Use when.**

- A primitive buffer is filled, then read, and the consumer accepts an
  `Array` (or an `ArraySeq` wrapping it).

**Do not use when.**

- The code removes or inserts elements: `ArrayBuilder` only appends.
- The consumer needs an `ArrayBuffer`: converting copies.

**Example.**

```scala
def primitive(n: Int): Array[Int] =
  val b = Array.newBuilder[Int] // int[] storage: no boxes
  b.sizeHint(n)
  var i = 0
  while i < n do { b += i * 1000; i += 1 }
  b.result()
```

Runnable: `BufferGrowth.primitive` in `Collections.scala`.

**Cost removed.** Measured, 1,000 elements: 20,104 B/op (presized
`ArrayBuffer[Int]`) versus 4,040 B/op.

**Verify.**

1. `PASS buffer-primitive` (same elements).
1. `PASS buffer-primitive allocation (...)` (asserts at most 50%).

## Array.newBuilder with an exact sizeHint

**Definition.** `sizeHint(n)` gives the primitive `ArrayBuilder.ofInt`
from `Array.newBuilder[Int]` capacity n up front ([Builder][builder]).
Without it the builder grows by copying. When capacity equals size,
`result()` returns the internal array without a copy
([ArrayBuilder source][arraybuilder]).

**Use when.**

- The final size is known (or bounded) before the loop.

**Do not use when.**

- The hint would be a guess much larger than the result: the builder
  allocates the hint and then copies down to the real size.
- A preallocated `Array[Int]` filled by index fits: it is simpler.

**Example.**

```scala
def candidate(n: Int): Array[Int] =
  val b = Array.newBuilder[Int]
  b.sizeHint(n) // exact capacity: no regrowth, result() returns it
  var i = 0
  while i < n do { b += i; i += 1 }
  b.result()
```

Runnable: `SizedBuilder` in `Collections.scala`.

**Cost removed.** Measured, 1,000 elements: 12,280 B/op versus
4,040 B/op.

**Verify.**

1. `PASS sized-builder`.
1. `PASS sized-builder allocation (...)` (asserts at most 50%).

## StringBuilder instead of string concatenation in a fold

**Definition.** `parts.foldLeft("")(_ + _)` creates a new `String` per
step and copies everything so far (quadratic). A
`java.lang.StringBuilder` presized to the total length appends in
amortized constant (aC) time ([performance characteristics][perf]).

**Use when.**

- Strings are joined in a loop or fold, or with `+=` on a `String`
  var.

**Do not use when.**

- `mkString` expresses it: it already uses a builder internally.
- A single expression concatenates a fixed number of parts: Scala 3
  compiles `s"..."` and `+` chains to one `makeConcatWithConstants` call
  (see the interpolation card in the language reference).

**Example.**

```scala
def candidate(parts: List[String]): String =
  val sb = new java.lang.StringBuilder(parts.foldLeft(0)(_ + _.length))
  parts.foreach(sb.append)
  sb.toString
```

Runnable: `StringJoin` in `Collections.scala`.

**Cost removed.** Measured, 300 parts: 346,720 B/op versus
9,144 B/op.

**Verify.**

1. `PASS string-join` and `PASS string-join-empty`.
1. `PASS string-join allocation (...)` (asserts at most 5%).

## mutable.HashMap instead of folding an immutable Map

**Definition.** `m.updated(k, v)` on an immutable `HashMap` returns a
new map that shares structure but allocates new trie nodes on every
update; `mutable.HashMap.updateWith` updates in place ([HashMap][mhashmap];
absent from the 2.12 sources). Both are eC per operation
([performance characteristics][perf]).

**Use when.**

- A fold or loop builds a map with many updates, and nothing observes
  the intermediate maps.

**Do not use when.**

- Intermediate versions are shared or retained (undo, snapshots,
  concurrent readers): the mutable map would expose later writes.
- The map escapes to other threads without synchronization.
- The caller needs an immutable `Map`: add `.toMap` and count its cost.

**Example.**

```scala
def mutableHashMap(words: Array[String]): mutable.HashMap[String, Int] =
  val m = mutable.HashMap.empty[String, Int]
  var i = 0
  while i < words.length do
    m.updateWith(words(i)) {
      case Some(c) => Some(c + 1)
      case None    => Some(1)
    }
    i += 1
  m
```

Runnable: `WordCount` in `Collections.scala`.

**Cost removed.** Measured, 5,000 words over 50 keys: 1,487,008 B/op
(immutable fold) versus 162,048 B/op; the remainder is one `Some` and
one boxed count per update. JMH: `countImmutable`
495,184 ± 154,335 ns/op, `countMutable` 397,378 ± 269,376 ns/op. The
intervals overlap, so only the byte reduction is established.

**Verify.**

1. `PASS wordcount-mutable` (compared with `.toMap`).
1. `PASS wordcount-mutable allocation (...)`.

## java.util.HashMap.merge for counting

**Definition.** `java.util.HashMap.merge(key, value, fn)` inserts
`value` or replaces the current value with `fn(old, value)` in one
lookup ([HashMap.merge][jhashmap]). `Integer` counts are boxed, but no
update creates an `Option`.

**Use when.**

- A counting or accumulating loop is hot, the map stays private to the
  method or is converted once, and Java interop is acceptable.

**Do not use when.**

- The map is exposed as a Scala `Map`: the conversion copies it.
- `fn` returns `null`: `merge` then removes the key, which a Scala map
  never does.

**Example.**

```scala
def javaHashMap(words: Array[String])
    : java.util.HashMap[String, Integer] =
  val m = new java.util.HashMap[String, Integer]()
  val one: Integer = 1
  var i = 0
  while i < words.length do
    m.merge(words(i), one, (a, b) => a + b)
    i += 1
  m
```

Runnable: `WordCount.javaHashMap` in `Collections.scala`.

**Cost removed.** Measured, 5,000 words over 50 keys: 2,672 B/op versus
1,487,008 B/op for the immutable fold (counts up to 100 stay inside the
`Integer` cache here; larger counts box). JMH: `countJava`
178,425 ± 81,698 ns/op versus `countImmutable` 495,184 ± 154,335 ns/op.

**Verify.**

1. `PASS wordcount-java`.
1. `PASS wordcount-java allocation (...)`.

## Slot array for counters keyed by a small set

**Definition.** Map each key to a dense slot index once
(`getOrElseUpdate(key, slot.size)`) and keep the counters in an
`Array[Int]`; increments then allocate no boxes or `Option`s.

**Use when.**

- The number of distinct keys is small relative to the number of
  updates, and counters are primitive.

**Do not use when.**

- Keys are unbounded: the array must be sized for the worst case.
- Only a handful of updates happen: the extra structure costs more than
  it saves.

**Example.**

```scala
def slotCounts(words: Array[String]): Map[String, Int] =
  val slot = mutable.HashMap.empty[String, Int]
  val counts = new Array[Int](words.length)
  var i = 0
  while i < words.length do
    counts(slot.getOrElseUpdate(words(i), slot.size)) += 1
    i += 1
  slot.iterator.map((w, s) => w -> counts(s)).toMap
```

Runnable: `WordCount.slotCounts` in `Collections.scala`.

**Cost removed.** Measured: 162,048 B/op (`updateWith`) versus
35,160 B/op, including the final immutable `Map`.

**Verify.**

1. `PASS wordcount-slots`.
1. `PASS wordcount-slots allocation (...)` (asserts at most 50% of the
   `updateWith` version).

## groupMapReduce instead of groupBy and mapValues

**Definition.** `groupMapReduce(key)(f)(reduce)` maps and reduces
values per key in one pass without materializing the groups
([IterableOps][iterableops]; absent from the 2.12 sources).

**Use when.**

- Readability: one call replaces `groupBy(...).view.mapValues(...)`.
- Groups are large and retained memory matters: the group collections
  are never built.

**Do not use when.**

- The goal is lower allocation for small groups: 3,000 strings over
  40 keys measured 95,848 B/op for `groupBy(identity).view
  .mapValues(_.size).toMap` and 105,248 B/op for `groupMapReduce`, so the
  candidate allocated more. The oracle prints this as `INFO`, not a
  pass.

**Example.**

```scala
def baseline(xs: List[String]): Map[String, Int] =
  xs.groupBy(identity).view.mapValues(_.size).toMap
def candidate(xs: List[String]): Map[String, Int] =
  xs.groupMapReduce(identity)(_ => 1)(_ + _)
```

Runnable: `GroupCount` in `Collections.scala`.

**Cost removed.** None measured (see above). Keep it only if a
measurement on the real key and group distribution shows a gain.

**Verify.**

1. `PASS group-count` (equal maps).
1. Read the `INFO group-count` line; confirm with `-prof gc` on real data.

## Set for repeated membership tests

**Definition.** `List.contains` compares against every element (L);
`Set.contains` on a `HashSet` hashes once and compares only colliding
entries (eC) ([performance characteristics][perf]).

**Use when.**

- `contains`, `exists(_ == x)`, or `indexOf` on a `Seq` runs inside a
  loop over another collection.

**Do not use when.**

- The collection is tiny and queried once: building the set costs
  more.
- Elements have mutable fields used by `equals`/`hashCode`: a mutated
  element is lost in a hash set.
- Duplicates or order matter to the output: `toSet` drops duplicates
  (asserted by `PASS toSet drops duplicates`).

**Example.**

```scala
def baseline(members: List[CountedKey], qs: Array[CountedKey]): Int =
  qs.count(members.contains)

def candidate(members: List[CountedKey], qs: Array[CountedKey]): Int =
  val set = members.toSet
  qs.count(set.contains)
```

Runnable: `Membership` in `Collections.scala`; `CountedKey` counts
`equals` calls.

**Cost removed.** `equals` calls, deterministic: 500 members and 500
queries made 187,500 calls with `List.contains` and 260 with a `Set`.

**Verify.**

1. `PASS membership` (same count).
1. `PASS membership equals calls (List.contains 187500 equals calls,
   Set.contains 260)`.

[integer-cache]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Integer.html#valueOf(int)
[perf]: https://docs.scala-lang.org/overviews/collections-2.13/performance-characteristics.html
[arrayseq]: https://www.scala-lang.org/api/3.x/scala/collection/immutable/ArraySeq.html
[listbuffer]: https://github.com/scala/scala3/blob/main/library/src/scala/collection/mutable/ListBuffer.scala
[iterableonce]: https://github.com/scala/scala3/blob/main/library/src/scala/collection/IterableOnce.scala
[arraybuilder]: https://github.com/scala/scala3/blob/main/library/src/scala/collection/mutable/ArrayBuilder.scala
[iterators]: https://docs.scala-lang.org/overviews/collections-2.13/iterators.html
[views]: https://docs.scala-lang.org/overviews/collections-2.13/views.html
[builder]: https://www.scala-lang.org/api/3.x/scala/collection/mutable/Builder.html
[arraybuffer]: https://www.scala-lang.org/api/3.x/scala/collection/mutable/ArrayBuffer.html
[arraybuffer-src]: https://github.com/scala/scala3/blob/main/library/src/scala/collection/mutable/ArrayBuffer.scala
[mhashmap]: https://www.scala-lang.org/api/3.x/scala/collection/mutable/HashMap.html
[jhashmap]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html#merge(K,V,java.util.function.BiFunction)
[iterableops]: https://www.scala-lang.org/api/3.x/scala/collection/IterableOps.html
