# Collections, sequences, and strings

Collection pipelines and string building. Pairs live in
[`Collections.kt`][Collections.kt].
`verify.sh verify collections` runs the oracles and allocation checks,
`verify.sh bytecode` the `javap` assertions, and `verify.sh measure` the
JMH pairs. Numbers are machine-specific (see
[measurement](measurement.md)). Byte counts come from the thread counter
with default escape analysis unless marked otherwise.

Tier: Executed. `verify collections`, `noea`, `bytecode`, `benchmark`,
`measure`, and `jfr` ran locally for every card in this file.

## Contents

- Sequence for a multi-step chain that stops early
- Sequence versus Iterable for short chains
- Materialize a Sequence that is consumed more than once
- sumOf instead of map then sum
- buildList with capacity instead of list plus element
- buildString instead of string += in a loop
- String templates
- groupingBy eachCount instead of groupBy mapValues
- associateWith instead of associate with Pair

## Sequence for a multi-step chain that stops early

**Definition.** Iterable operations are eager: each step "completes and
returns its result as an intermediate collection". A `Sequence` runs all
steps per element, only when a terminal operation asks, so `take(n)`
stops the chain after `n` results ([sequences][seq]).

**Use when.**

- A chain of two or more steps over a large collection ends in `take`,
  `first`, `firstOrNull`, `any`, or `find`, and most elements are never
  needed.

**Do not use when.**

- The caller relies on lambda side effects: the eager chain runs `map` on
  every element, the lazy chain only on the elements it pulls (the oracle
  counts 3 calls vs 1 for `take(1)` of three).
- The chain is short and consumed fully (next card).
- Exceptions must surface at the same point: a lazy chain throws when the
  terminal operation runs, not when the chain is built.

**Example.**

```kotlin
fun firstSquaresCandidate(values: List<Int>, limit: Int): List<Int> =
    values.asSequence().filter { it % 2 == 0 }.map { it * it }
        .take(limit).toList()
```

Runnable: `firstSquaresBaseline` / `firstSquaresCandidate`.

**Cost removed.** The two intermediate lists. Measured (10,000 elements,
`take(10)`): baseline 175,216 B/call, candidate 328 B/call. JMH:
`takeBaseline` 57,323 ± 39,019 ns/op, 175,216 B/op; `takeCandidate`
61.8 ± 2.9 ns/op, 240 B/op. The baseline error is wide on the shared
machine, but the gap is three orders of magnitude.

**Verify.**

1. `verify.sh verify collections`: `sequence take` for limits 0, 1, 10,
   and 20,000 (more than available), plus both side-effect counts.
1. `verify.sh verify collections`: `PASS alloc sequence take 10`.

## Sequence versus Iterable for short chains

**Definition.** A sequence adds one wrapper object per step plus
iterators, which "adds overhead that may be significant when processing
smaller collections or doing simpler computations" ([sequences][seq]).

**Use when.**

- Someone claims either direction ("sequences are always slower on small
  lists" or "always use sequences") for a chain that consumes every
  element: measure that chain on the target JDK before choosing.

**Do not use when.**

- The chain stops early or the collection is large: the previous card
  applies without a new measurement.

**Example.**

```kotlin
fun smallChainIterable(values: List<Int>): Int =
    values.filter { it > 0 }.map { it * 2 }.sum()

fun smallChainSequence(values: List<Int>): Int =
    values.asSequence().filter { it > 0 }.map { it * 2 }.sum()
```

**Cost removed.** Measured with 16 elements, and the result contradicts
the documented caution on this JDK: thread counter Iterable 152 B/call,
Sequence 0 B/call (C2 removed the sequence wrappers; without escape
analysis 248 B vs 152 B). JMH: `smallIterable` 64.2 ± 7.6 ns/op,
104 B/op; `smallSequence` 16.1 ± 0.4 ns/op, 0 B/op. The overhead the docs
warn about exists in the bytecode, but the JIT erased it here. Other
lambdas, sizes, or JDKs can differ.

**Verify.**

1. `verify.sh verify collections`: `PASS small chain`.
1. `verify.sh verify collections` prints the `INFO alloc small chain`
   line; `BENCH_FILTER=small sh assets/examples/verify.sh measure`.

## Materialize a Sequence that is consumed more than once

**Definition.** A sequence built from operations is a recipe: every
terminal operation re-runs the whole chain, source included.
"Sequences can be iterated multiple times" unless an implementation says
otherwise ([sequences][seq]), and each iteration repeats the work.

**Use when.**

- The same `Sequence` value feeds two terminal operations (`sum()` then
  `count()`, or two `toList()` calls), and its source is expensive or has
  side effects.

**Do not use when.**

- The sequence is consumed once: `toList()` only adds a list.
- It is a one-shot sequence (`constrainOnce()`, or a wrapped
  `Iterator`): the second use throws, so fix the design instead of
  caching.

**Example.**

```kotlin
fun sequenceTwiceCandidate(source: () -> Int): Pair<Int, Int> {
    val values =
        generateSequence(1) { it + 1 }.take(4).map { it + source() }.toList()
    return values.sum() to values.size
}
```

**Cost removed.** The second evaluation. Oracle: the baseline calls
`source` 8 times for 4 elements, the candidate 4 times, with equal
results.

**Verify.**

1. `verify.sh verify collections`: `sequence reuse baseline calls` (8)
   and `sequence reuse candidate calls` (4).

## sumOf instead of map then sum

**Definition.** `map { }.sum()` builds a `List<Int>` of boxed values and
then sums it. `sumOf { }` (Kotlin 1.4+, [sumOf][sumof]) is an inline
loop over the source with a primitive accumulator.

**Use when.**

- A reduction (`sum`, `max`, `count`) runs over a mapped collection that
  nothing else uses.

**Do not use when.**

- The mapped list is also used afterwards; compute it once.
- The selector returns `Int` and the sum can overflow `Int`: `sumOf`
  keeps the selector's type. Select `it.toLong()` to widen, as the
  baseline would also need.

**Example.**

```kotlin
fun totalLengthCandidate(words: List<String>): Int =
    words.sumOf { it.length }
```

**Cost removed.** The intermediate `ArrayList`, and one `Integer` per
element above 127. Measured (1,000 words): baseline 4,040 B/call,
candidate 0 B/call. Bytecode: `Integer.valueOf` only in the baseline.
JMH: `sumOfBaseline` 49,212 ± 42,862 ns/op, 4,040 B/op; `sumOfCandidate`
948.1 ± 1,005 ns/op, 0 B/op. Time errors were large in two runs on a
shared machine: claim the bytes, and claim time only from a quiet rerun.

**Verify.**

1. `verify.sh verify collections`: `PASS sumOf`, `PASS alloc sumOf`.
1. `verify.sh bytecode`: `totalLengthCandidate` has no `Integer.valueOf`.

## buildList with capacity instead of list plus element

**Definition.** `list + element` on a read-only `List` copies the whole
list, so appending in a loop is quadratic.
`buildList(capacity) { add(...) }` (Kotlin 1.6+, [buildList][buildlist])
fills one presized `MutableList` and returns it read-only.

**Use when.**

- A loop grows a `List` with `result = result + x`, or with `+=` on a
  `var` of a read-only type.

**Do not use when.**

- Each intermediate list is kept (persistent snapshots). Use a
  persistent collection library instead.
- The capacity is unknown or can be negative: `buildList` throws
  `IllegalArgumentException` on a negative capacity, so omit it.

**Example.**

```kotlin
fun appendCandidate(values: IntArray): List<Int> =
    buildList(values.size) { for (value in values) add(value) }
```

**Cost removed.** n list copies. Measured (1,000 elements): baseline
4,075,568 B/call, candidate 19,632 B/call (list plus `Integer` boxes).

**Verify.**

1. `verify.sh verify collections`: `PASS buildList`, empty input.
1. `PASS alloc buildList`.

## buildString instead of string += in a loop

**Definition.** `out += "$part;"` creates a new `String` each iteration,
copying everything so far. `buildString(capacity) { }` appends into one
`StringBuilder` and calls `toString()` once.

**Use when.**

- A loop concatenates onto a `String` variable.

**Do not use when.**

- The pieces are already in a collection and only need a separator:
  `joinToString(";")` is the same builder in one call and reads better.
- A few fixed pieces are joined once: a template is enough.

**Example.**

```kotlin
fun joinCandidate(parts: List<String>): String =
    buildString(parts.sumOf { it.length + 1 }) {
        for (part in parts) append(part).append(';')
    }
```

**Cost removed.** Quadratic copying. Measured (503 parts including empty,
`é`, and an emoji): baseline 607,744 B/call, candidate 12,080 B/call.
JMH (500 parts): `joinBaselineBench` 22,223 ± 4,659 ns/op, 598,040 B/op;
`joinCandidateBench` 3,403 ± 420.1 ns/op, 4,840 B/op.

**Verify.**

1. `verify.sh verify collections`: `PASS buildString` including
   non-ASCII parts, and the empty case.
1. `verify.sh bytecode`: `makeConcatWithConstants` in `joinBaseline`,
   none in `joinCandidate`.

## String templates

**Definition.** On JVM 9+ targets, Kotlin 1.5.20+ compiles string
templates and `+` to an `invokedynamic` call of
`StringConcatFactory.makeConcatWithConstants`. `-Xstring-concat=inline`
restores `StringBuilder` chains ([Kotlin 1.5.20][concat]).

**Use when.**

- One expression builds a string from a fixed number of parts:
  `"user-$id:$name"` is already the efficient form. Do not rewrite it as
  a manual `StringBuilder`.

**Do not use when.**

- The template sits in an accumulating loop (`+=`): see the
  `buildString` card.
- The project targets `jvmTarget` 1.8: concatenation is a
  `StringBuilder` chain there (checked with `kotlinc -jvm-target 1.8` and
  `javap`), so the bytecode claim does not apply.

**Example.**

```kotlin
fun labelTemplate(id: Int, name: String): String = "user-$id:$name"
```

**Cost removed.** Nothing; the card prevents a pointless rewrite.
Bytecode: one `invokedynamic makeConcatWithConstants`.

**Verify.**

1. `verify.sh verify collections`: `PASS template`.
1. `verify.sh bytecode`: `labelTemplate` matches
   `makeConcatWithConstants`.

## groupingBy eachCount instead of groupBy mapValues

**Definition.** `groupBy { }` builds a `List` per key, and `mapValues`
then builds a second map. `groupingBy { }` returns a lazy `Grouping`
(Kotlin 1.1+, [groupingBy][groupingby]), and `eachCount()` folds each
key to a count without per-key lists.

**Use when.**

- The code counts or folds groups (`size`, `sum`) and discards the group
  lists.

**Do not use when.**

- The group members are needed afterwards.

**Example.**

```kotlin
fun countsCandidate(words: List<String>): Map<String, Int> =
    words.groupingBy { it }.eachCount()
```

**Cost removed.** One list per key and the second map. Measured (1,000
words, 37 keys): baseline 19,272 B/call, candidate 2,704 B/call. JMH:
`countsBaselineBench` 10,587 ± 705.6 ns/op, 19,272 B/op;
`countsCandidateBench` 16,205 ± 2,322 ns/op, 2,704 B/op. Fewer bytes but
**slower** here in both runs (first run 10,689 ± 1,494 vs
16,900 ± 4,892 ns/op): apply it for allocation or GC pressure, not for
time, unless your own measurement differs. The oracle confirmed the same
key iteration order (first occurrence), with NFC and NFD `é` as distinct
keys.

**Verify.**

1. `verify.sh verify collections`: `PASS groupingBy`,
   `PASS groupingBy order`.
1. `PASS alloc groupingBy`.

## associateWith instead of associate with Pair

**Definition.** `associate { it to f(it) }` creates a `Pair` per element.
`associateWith { f(it) }` (Kotlin 1.3+, [associateWith][assocwith]) puts
the key and value directly.

**Use when.**

- The keys are the elements themselves; it is also the clearer form.

**Do not use when.**

- You expect an allocation win with default flags: none was measured.

**Example.**

```kotlin
fun lengthsCandidate(words: List<String>): Map<String, Int> =
    words.associateWith { it.length }
```

**Cost removed.** **No difference** with escape analysis on: 48,272
B/call for both (1,000 keys), because C2 removed the `Pair`. Without
escape analysis: 72,304 B vs 48,304 B. Both forms keep the last value for
a duplicate key (the oracle includes one).

**Verify.**

1. `verify.sh verify collections`: `PASS associateWith`.
1. `verify.sh noea` prints the latent `Pair` cost.

[seq]: https://kotlinlang.org/docs/sequences.html
[sumof]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.collections/sum-of.html
[buildlist]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.collections/build-list.html
[concat]: https://kotlinlang.org/docs/whatsnew1520.html#string-concatenation-via-invokedynamic
[groupingby]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.collections/grouping-by.html
[assocwith]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.collections/associate-with.html
[Collections.kt]: ../assets/examples/constructs/src/main/kotlin/constructs/Collections.kt
