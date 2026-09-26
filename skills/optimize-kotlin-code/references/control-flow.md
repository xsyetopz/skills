# Loops, when, and lazy

How the compiler lowers range loops and `when`, and what each `lazy` mode
costs and guarantees. Pairs live in
[`ControlFlow.kt`][ControlFlow.kt].
`verify.sh verify control` runs the oracles, `verify.sh bytecode` the
`javap` assertions, `verify.sh measure` the JMH pairs. Numbers are
machine-specific (see [measurement](measurement.md)).

Tier: Executed. `verify control`, `noea`, `bytecode`, `benchmark`, and
`measure` ran locally for every card in this file.

## Contents

- Range loops the compiler lowers to counted loops
- Range objects from step, reversed, and forEach
- when over sealed types
- when over enum entries
- when over String constants
- lazy with SYNCHRONIZED (default)
- lazy with PUBLICATION
- lazy with NONE
- Eager val instead of lazy

## Range loops the compiler lowers to counted loops

**Definition.** A `for` loop directly over `0 until n`, `0..<n`, `a..b`,
`a downTo b`, `array.indices`, or `collection.indices` compiles to an
`int` counter with a compare-and-branch, with no `IntRange` object and no
iterator. Kotlin 2.4.20 `javap` output for the five catalog functions
contains no `kotlin/ranges` reference; they cover every form except
`a..b`, which a one-off `javap` of `for (i in a..b)` also showed as an
`if_icmpgt` loop with no `kotlin/ranges` reference. [ranges][ranges]
documents the operators, not the lowering; the lowering comes from local
`javap`.

**Use when.**

- Writing or reviewing an index loop in a hot path: put one of these
  forms directly in the `for` header.

**Do not use when.**

- You would replace a `for (x in array)` element loop with an index loop
  for speed: the element loop also lowers to a counted array loop.

**Example.**

```kotlin
fun sumIndices(xs: IntArray): Long {
    var s = 0L
    for (i in xs.indices) s += xs[i]
    return s
}
```

Runnable: `sumUntil`, `sumRangeUntil`, `sumIndices`, `sumDownTo`,
`sumListIndices`.

**Cost removed.** Range and iterator objects, compared with the next
card. JMH: `untilRange` 619.1 ± 52.8 ns/op, 0 B/op.

**Verify.**

1. `verify.sh verify control`: every `range ...` sum equals the `fold`
   result.
1. `verify.sh bytecode`: `kotlin/ranges` absent in all five functions.

## Range objects from step, reversed, and forEach

**Definition.** `0 until n step 2` calls `RangesKt.step` and creates an
`IntProgression`. `(0 until n).reversed()` calls `RangesKt.reversed`.
`(0 until n).forEach { }` creates an `IntRange` and iterates it through
`Iterable.iterator()` and `IntIterator.nextInt()`. In bytecode, all three
allocate per loop (local `javap`).

**Use when.**

- The profile or allocation counter shows `IntRange`, `IntProgression`,
  or `IntProgressionIterator` from a hot loop: rewrite it as a `while`
  loop with an explicit step, or use `downTo` for reverse order.

**Do not use when.**

- The loop runs once or rarely: the objects are small and the stepped
  form is clearer. `step` also validates its argument (a non-positive
  step throws `IllegalArgumentException`); keep that check if the step is
  an input.

**Example.**

```kotlin
fun sumEvenStepCandidate(xs: IntArray): Long {
    var s = 0L
    var i = 0
    while (i < xs.size) {
        s += xs[i]
        i += 2
    }
    return s
}
```

Runnable: `sumEvenStepBaseline` / `sumEvenStepCandidate`;
`sumForEachBaseline` and `sumReversedBaseline` against `sumUntil` and
`sumDownTo`.

**Cost removed.** Thread counter: `step` 48 B/call vs 0; `forEach` plus
`reversed` together 48 B/call vs 0 (escape analysis did not remove them;
104 B without it). JMH shows 0 B/op for both step forms, because escape
analysis removed the progression under JMH's inlining. Time was
**inconclusive**: `stepBaseline` 673.5 ± 518.7 ns/op, `stepCandidate`
4,056 ± 6,827 ns/op (first run 512.2 ± 517.5 vs 3,053 ± 4,018), with
errors larger than the scores on a shared machine. `forEachRange`
1,110 ± 101.1 ns/op vs `untilRange` 619.1 ± 52.8 ns/op, both 0 B/op.
Rewrite only when your own allocation profile shows range objects.

**Verify.**

1. `verify.sh verify control`: `range step` for sizes 0, 1, and 7 (odd
   length), `range forEach`, `range reversed`.
1. `verify.sh bytecode`: `RangesKt.step`, `Iterable.iterator`, and
   `RangesKt.reversed` in the baselines; no `kotlin/ranges` in
   `sumEvenStepCandidate`.

## when over sealed types

**Definition.** `when (shape) { is Square -> ...; is Circle -> ... }`
over a sealed hierarchy compiles to a chain of `instanceof` checks in
source order, ending in a `NoWhenBranchMatchedException` throw. Without
`else`, the compiler rejects the `when` if a subtype is missing
([sealed classes][sealed]).

**Use when.**

- Dispatching over a closed set of types. Keep it exhaustive and without
  `else`, so a new subtype is a compile error instead of a silent
  default.

**Do not use when.**

- You would reorder branches for speed without a profile: order matters
  only for many subtypes with a skewed distribution. Measure first.
- Branches overlap (`is Base` before `is Derived`): order then changes
  results, not just cost.

**Example.**

```kotlin
fun areaWhen(shape: Shape): Double = when (shape) {
    is Square -> shape.side * shape.side
    is Circle -> 3.0 * shape.radius * shape.radius
    is Rect -> shape.w * shape.h
}
```

**Cost removed.** None; the card records the lowering. `javap`: exactly
3 `instanceof` for 3 subtypes. JMH over 1,000 mixed shapes: `sealedWhen`
2,161 ± 343.1 ns/op, 0 B/op.

**Verify.**

1. `verify.sh verify control`: `PASS when sealed`.
1. `verify.sh bytecode`: `areaWhen` has 3 `instanceof`.

## when over enum entries

**Definition.** `when` over an enum compiles to a `tableswitch` on
`$EnumSwitchMapping$0[ordinal()]`, a mapping array in a synthetic
`$WhenMappings` class. Dispatch is constant time and independent of
entry order ([control flow][when]; lowering from local `javap`).

**Use when.**

- Mapping a closed enum to values or actions: keep the `when`.

**Do not use when.**

- You plan to replace it with a `HashMap<Enum, V>` or an `if` chain for
  speed: neither is faster than a `tableswitch`. `EnumMap` or an array
  indexed by `ordinal` helps only when the table must be data, not code.

**Example.**

```kotlin
fun weightWhen(level: Level): Int = when (level) {
    Level.DEBUG -> 1
    Level.INFO -> 2
    Level.WARN -> 4
    Level.ERROR -> 8
}
```

**Cost removed.** None; the card prevents a rewrite. `javap`:
`tableswitch` and `WhenMappings` in `weightWhen`.

**Verify.**

1. `verify.sh verify control`: `PASS when enum`.
1. `verify.sh bytecode`: the `tableswitch` and `WhenMappings` lines.

## when over String constants

**Definition.** `when (method) { "GET" -> ...; "PUT" -> ... }` compiles
to `String.hashCode()`, a `lookupswitch` on the hash values, and
`String.equals` against the candidate constant (local `javap`), like a
Java string `switch`.

**Use when.**

- Matching an input string against several constants: keep the `when`.

**Do not use when.**

- Matching must be case-insensitive or locale-aware: `when` compares
  exactly. Normalize the input once before the `when`, with an explicit
  `Locale.ROOT` if you lowercase.

**Example.**

```kotlin
fun methodWhen(method: String): Int = when (method) {
    "GET" -> 1
    "PUT" -> 2
    "POST" -> 3
    "DELETE" -> 4
    else -> 0
}
```

**Cost removed.** None; the card prevents a rewrite to a chain of `==`
checks. `javap`: `String.hashCode` and `lookupswitch`.

**Verify.**

1. `verify.sh verify control`: `PASS when string` (`"POST"` matches,
   `"post"` does not).
1. `verify.sh bytecode`: the `lookupswitch` and `String.hashCode` lines.

## lazy with SYNCHRONIZED (default)

**Definition.** `by lazy { }` uses `LazyThreadSafetyMode.SYNCHRONIZED`:
"only a single thread can initialize" the value
([LazyThreadSafetyMode][mode]), and `lazy(initializer)` "uses itself to
synchronize on" ([lazy][lazy]). The JVM implementation,
`SynchronizedLazyImpl`, reads a `volatile` field and enters a monitor
only while uninitialized ([LazyJVM.kt][lazyjvm]; `monitorenter` in its
`getValue` per `javap`).

**Use when.**

- The initializer is expensive or must run at most once (it opens a
  resource or has side effects), and several threads may read the value.

**Do not use when.**

- The value is always used and cheap: an eager `val` costs less (last
  card).
- External code may synchronize on the `Lazy` instance: the docs warn it
  can deadlock.
- The initializer can throw and you expect the failure to be cached: it
  "will attempt to reinitialize the value at next access" ([lazy][lazy]).

**Example.**

```kotlin
class ReportSync(private val rows: List<Int>) {
    val total: Int by lazy { rows.sum() }
}
```

**Cost removed.** The repeated work of computing on every access.
Oracle: with two threads racing, the initializer ran once.

**Verify.**

1. `verify.sh verify control`: `lazy synchronized initializer runs` = 1.
1. `verify.sh bytecode`: `SynchronizedLazyImpl.getValue` has
   `monitorenter`.

## lazy with PUBLICATION

**Definition.** `lazy(LazyThreadSafetyMode.PUBLICATION) { }` lets the
initializer run "several times on concurrent access", but publishes only
one result to all threads ([LazyThreadSafetyMode][mode]). The JVM
implementation publishes with a `compareAndSet` instead of a lock.

**Use when.**

- The initializer is pure and cheap enough to run twice, and readers must
  never block on a lock (for example, code on coroutine dispatcher
  threads).

**Do not use when.**

- The initializer has side effects or acquires resources: it can run
  more than once. The oracle forces a race and counts 2 runs.

**Example.**

```kotlin
class ReportPublication(private val rows: List<Int>) {
    val total: Int by lazy(LazyThreadSafetyMode.PUBLICATION) { rows.sum() }
}
```

**Cost removed.** Concurrent first readers no longer block on a monitor.

**Verify.**

1. `verify.sh verify control`: `lazy publication initializer runs` = 2
   and `PASS lazy publication` (value correct).
1. `verify.sh bytecode`: `SafePublicationLazyImpl.getValue` has
   `compareAndSet`.

## lazy with NONE

**Definition.** `lazy(LazyThreadSafetyMode.NONE) { }` takes no locks: "if
the instance is accessed from multiple threads, its behavior is
unspecified" ([LazyThreadSafetyMode][mode]). `UnsafeLazyImpl` uses a
plain field.

**Use when.**

- The owning object is confined to one thread (a UI thread, a
  single-threaded actor, or a dispatcher view with parallelism 1).

**Do not use when.**

- Any other thread can read it: behavior is unspecified. The initializer
  can run more than once, and `_value` is a plain, non-volatile field in
  `UnsafeLazyImpl`.
- You expect lower memory per instance: a `ReportNone` and a
  `ReportSync` both allocate 64 B per instance (the `Lazy` object plus
  the initializer lambda). NONE saves synchronization, not bytes.

**Example.**

```kotlin
class ReportNone(private val rows: List<Int>) {
    val total: Int by lazy(LazyThreadSafetyMode.NONE) { rows.sum() }
}
```

**Cost removed.** The volatile read and the monitor on first access.
JMH steady-state read: `lazySyncRead` 2.4 ± 1.7 ns/op, 0 B/op;
`lazyNoneRead` 1.5 ± 0.8 ns/op, 0 B/op. These are within error of each
other, so NONE bought no measurable read speed here.

**Verify.**

1. `verify.sh verify control`: `PASS lazy none`; the `INFO alloc lazy per
   instance (none vs sync)` line.
1. `verify.sh bytecode`: `UnsafeLazyImpl.getValue` has neither
   `monitorenter` nor `compareAndSet`.

## Eager val instead of lazy

**Definition.** A plain `val` computed in the constructor stores the
result directly. `by lazy` adds a `Lazy` object and a lambda capturing
`this` to every instance, plus a delegate call on every read.

**Use when.**

- Many instances are created, most of them read the property, and the
  computation is cheap or needed anyway.

**Do not use when.**

- The value is often unused and expensive, or depends on state that is
  not ready in the constructor.

**Example.**

```kotlin
class ReportEager(rows: List<Int>) {
    val total: Int = rows.sum()
}
```

**Cost removed.** Measured per instance: `ReportSync` 64 B vs
`ReportEager` 16 B (the object itself). JMH read: `eagerRead`
0.7 ± 0.2 ns/op, 0 B/op vs `lazySyncRead` 2.4 ± 1.7 ns/op, 0 B/op.

**Verify.**

1. `verify.sh verify control`: `lazy sync` value equals the eager sum.
1. `PASS alloc lazy per instance (sync vs eager)`.

[ranges]: https://kotlinlang.org/docs/ranges.html
[sealed]: https://kotlinlang.org/docs/sealed-classes.html
[when]: https://kotlinlang.org/docs/control-flow.html
[mode]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/
[lazy]: https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/lazy.html
[lazyjvm]: https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt
[ControlFlow.kt]: ../assets/examples/constructs/src/main/kotlin/constructs/ControlFlow.kt
