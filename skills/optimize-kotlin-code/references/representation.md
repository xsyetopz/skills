# Data representation

How values are laid out and accessed: value classes, primitive arrays,
nullable primitives, constants, JVM field and static annotations, and
data classes. Pairs live in
[`Representation.kt`][Representation.kt]
and
[`Consts.kt`][Consts.kt].
Byte counts come from the thread allocation counter after warm-up with
`-Xbatch` and default escape analysis. JMH rows are `Score ± Error` ns/op
and `gc.alloc.rate.norm` B/op. Machine and toolchain: see
[measurement](measurement.md).

Tier: Executed. `verify representation`, `noea`, `bytecode`,
`benchmark`, and `measure` ran locally for every card in this file.

## Contents

- Value class used as its own type
- Value class boxing at generic, nullable, and interface boundaries
- Primitive arrays instead of List of Int and Array of Int
- Non-null primitive locals instead of Int?
- const val instead of val
- JvmField on properties read by Java or across classes
- JvmStatic on companion functions
- Local accumulators instead of data class copy in a loop
- Explicit equals order for hot keys

## Value class used as its own type

**Definition.** `@JvmInline value class Cents(val value: Long)` wraps one
value in a distinct type. Where the static type is `Cents`, the compiler
passes the underlying `long`, and functions taking it get mangled JVM
names such as `Cents.plus-7-1qKwI(long, long)` in the catalog
([value classes][vc]). The JVM requires `@JvmInline`.

**Use when.**

- A hot loop creates a domain wrapper (IDs, money, units) per element,
  and the allocation counter or JFR shows the wrapper class.

**Do not use when.**

- The wrapper needs more than one property, identity (`===`), or a
  mutable field: a value class allows one read-only property.
- Java must call the function: Java cannot call mangled names without
  `@JvmName`.
- The value will mostly travel through generic, nullable, or interface
  types: it is boxed there (next card), which can allocate more than a
  regular class.

**Example.**

```kotlin
@JvmInline
value class Cents(val value: Long) {
    operator fun plus(other: Cents) = Cents(value + other.value)
}

fun totalCandidate(prices: LongArray): Cents {
    var total = Cents(0)
    for (price in prices) total += Cents(price)
    return total
}
```

Runnable: `totalBaseline` (regular `class CentsBox`) and
`totalCandidate` in `Representation.kt`.

**Cost removed.** One wrapper object per addition. Measured (1,000
prices): baseline 24,024 B/call, candidate 0 B/call. Escape analysis did
not remove the baseline objects, because `total` is reassigned in the
loop. Bytecode: `totalBaseline` contains `new CentsBox`; `totalCandidate`
contains no `new`, and its JVM return type is `long`.

**Verify.**

1. `sh assets/examples/verify.sh verify representation`:
   `PASS value class total` and `PASS alloc value class total`.
1. `verify.sh bytecode`: `totalCandidate` has no `new`.

## Value class boxing at generic, nullable, and interface boundaries

**Definition.** "Inline classes are boxed whenever they are used as
another type" ([value classes][vc-repr]): as a type argument
(`List<Cents>`), as a nullable type (`Cents?`), or as an interface they
implement. Boxing calls the generated `box-impl`, which allocates.

**Use when.**

- `javap` shows `"box-impl"` in a hot path, or JFR shows the value class
  itself among allocated types.
- Many values are stored: keep the underlying primitive array and expose
  a value-class view, as the stdlib `ULongArray` does over `LongArray`.

**Do not use when.**

- An API requires a `List`: converting at the boundary allocates anyway.
- The nullable form is rare and cold: boxing once does not justify an
  API change.

**Example.**

```kotlin
@JvmInline
value class CentsArray(val raw: LongArray) {
    val size: Int get() = raw.size

    operator fun get(index: Int): Cents = Cents(raw[index])
}

fun pricesCandidate(raw: LongArray): CentsArray = CentsArray(raw.copyOf())
```

Runnable: `pricesBaseline` (`raw.map { Cents(it) }`), `pricesCandidate`,
and `firstOrNullBaseline` (returns `Cents?`) in `Representation.kt`.

**Cost removed.** One box per element plus the list. Measured (1,000
values): baseline 28,040 B/call, candidate 8,016 B/call (one `long[]`).

**Verify.**

1. `verify.sh verify representation`: `value class storage` checks size
   and every element; nullable checks cover present and empty.
1. `verify.sh bytecode`: `pricesBaseline` contains `Cents."box-impl"`.

## Primitive arrays instead of List of Int and Array of Int

**Definition.** `IntArray` compiles to `int[]`. `List<Int>` and
`Array<Int>` hold `java.lang.Integer` references, and each element
outside the range that `Integer.valueOf` must cache (-128 to 127,
[Integer.valueOf][valueof]) is a separate object.

**Use when.**

- Numeric data is built or scanned in bulk, and the profile shows
  `Integer.valueOf`, `Integer` allocation, or `intValue` calls.

**Do not use when.**

- The data needs `null` elements or goes to APIs that take `List<Int>`:
  converting back allocates everything again.
- All values are in -128..127: boxes come from the cache, and the saving
  is only the reference indirection.

**Example.**

```kotlin
fun squaresBaseline(n: Int): List<Int> = List(n) { (it + 200) * 3 }

fun squaresCandidate(n: Int): IntArray = IntArray(n) { (it + 200) * 3 }
```

Runnable: `squaresBaseline`, `squaresArrayBaseline` (`Array<Int>`), and
`squaresCandidate` in `Representation.kt`.

**Cost removed.** 1,000 `Integer` objects. Measured: `List<Int>` 20,040
B/call, `Array<Int>` 20,016 B/call, `IntArray` 4,016 B/call. JMH:
`boxedListBaseline` 2,372 ± 303.5 ns/op, 20,040 B/op;
`boxedListCandidate` 244.7 ± 20.5 ns/op, 4,016 B/op.

**Verify.**

1. `verify.sh verify representation`: `PASS primitive array` and
   `PASS boxed array` compare contents.
1. `verify.sh bytecode`: `Integer.valueOf` in both baselines, absent in
   `squaresCandidate`.

## Non-null primitive locals instead of Int?

**Definition.** A local of type `Int?` is a `java.lang.Integer`
reference: every assignment boxes and every comparison unboxes. A
non-null `Int` local is a JVM `int`.

**Use when.**

- A loop tracks a "best so far" or "maybe found" value in an `Int?`,
  `Long?`, or `Double?`, and `javap` shows `Integer.valueOf` or
  `intValue` inside the loop.

**Do not use when.**

- The function boxes the nullable value only once, at the return: that
  box is cheap and the `Int?` result type needs it anyway.

**Example.**

```kotlin
fun maxOrNullCandidate(values: IntArray): Int? {
    if (values.isEmpty()) return null
    var best = values[0]
    for (i in 1 until values.size) if (values[i] > best) best = values[i]
    return best
}
```

Runnable: `maxOrNullBaseline` / `maxOrNullCandidate` in
`Representation.kt`.

**Cost removed.** One `Integer` per improvement. Measured (1,000
increasing values from 1,000): baseline 15,984 B/call, candidate 0 B/call
(the harness subtracts the single returned box). JMH:
`nullableBaseline` 702.0 ± 102.2 ns/op, 2,064 B/op; `nullableCandidate`
272.1 ± 95.6 ns/op, 16 B/op. The JMH input is 0..999 permuted, so it has
fewer improvements and some cached boxes compared with the oracle input.

**Verify.**

1. `verify.sh verify representation`: `nullable local` cases for empty,
   one negative value, and a mixed array.
1. `verify.sh bytecode`: `Integer.intValue` in `maxOrNullBaseline`, none
   in `maxOrNullCandidate`.

## const val instead of val

**Definition.** A `const val` of primitive or `String` type is a
compile-time constant, "inlined at compile time" at each use
([Java interop][interop-static]). A top-level `val` read from another
file is a call to its getter (`getPLAIN_BUFFER_SIZE()`).

**Use when.**

- The value is a literal known at compile time and used in expressions,
  annotations, or `when` branches.

**Do not use when.**

- The value can change between releases of a library: callers compiled
  against the old value keep it until they are recompiled.
- The value is computed at run time or is not a primitive or `String`:
  the compiler rejects `const` there.

**Example.**

```kotlin
// Consts.kt
val PLAIN_BUFFER_SIZE = 8_192
const val CONST_BUFFER_SIZE = 8_192

// Representation.kt
fun bufferSizeCandidate(): Int = CONST_BUFFER_SIZE * 2
```

**Cost removed.** A static call and the multiplication: the candidate
body is `sipush 16384; ireturn`, folded at compile time, while the
baseline calls `getPLAIN_BUFFER_SIZE` and multiplies. No timing claim:
C2 inlines trivial static getters, so measure before claiming speed.

**Verify.**

1. `verify.sh verify representation`: `PASS const val`.
1. `verify.sh bytecode`: `sipush 16384` and no `invokestatic` in
   `bufferSizeCandidate`.

## JvmField on properties read by Java or across classes

**Definition.** `@JvmField` exposes a property's backing field directly
and generates no getter or setter. The property needs a backing field
and cannot be `private`, `open`, `override`, `const`, or delegated
([Java interop][interop-field]). Kotlin call sites then use `getfield`
instead of `invokevirtual getX()`.

**Use when.**

- Java code reads the property in a hot loop, or the class is a plain
  data carrier shared with Java.

**Do not use when.**

- The property may later need a custom getter, validation, or an `open`
  override: switching back changes the binary interface for Java.
- You expect a Kotlin-only speedup: C2 inlines trivial getters, and no
  timing difference was measured for this card.

**Example.**

```kotlin
class Point(x: Int, y: Int) {
    val x: Int = x

    @JvmField
    val y: Int = y
}
```

**Cost removed.** A getter call in bytecode: `readPropertyBaseline` has
`invokevirtual Point.getX`, and `readPropertyCandidate` has
`getfield Point.y`.

**Verify.**

1. `verify.sh verify representation`: `PASS jvmfield/jvmstatic`.
1. `verify.sh bytecode`: the `getX` and `getfield` assertions.

## JvmStatic on companion functions

**Definition.** `@JvmStatic` on a companion or object function also
generates a static method on the enclosing class, so Java can call
`Point.originStatic()`. The instance method on `Companion` remains
([Java interop][interop-static-methods]).

**Use when.**

- Java callers need a static entry point (static factories, `main`,
  frameworks that look up static methods).

**Do not use when.**

- You expect Kotlin call sites to change: kotlinc 2.4.20 still compiles
  the Kotlin call as `getstatic Point.Companion` plus
  `invokevirtual Point$Companion.originStatic` (checked by `javap`). It
  removes no Kotlin-side cost.

**Example.**

```kotlin
companion object {
    fun origin(): Int = 0

    @JvmStatic
    fun originStatic(): Int = 0
}
```

**Cost removed.** For Java callers, the `Companion` field load. For
Kotlin callers, nothing (bytecode confirms no change).

**Verify.**

1. `verify.sh bytecode`: `readPropertyCandidate` still matches
   `Point\$Companion.originStatic`.
1. `javap -p -cp target/classes constructs.Point` lists a `static`
   `originStatic()` next to the companion method.

## Local accumulators instead of data class copy in a loop

**Definition.** `copy(...)` on a data class calls the constructor with
the changed and unchanged properties, creating one object per call.
Folding state in local variables and constructing the data class once
removes the per-iteration objects.

**Use when.**

- A loop or `fold` updates an immutable data class state with `copy` per
  element, and the allocation counter or JFR shows that class.

**Do not use when.**

- Intermediate states are published (emitted to a `StateFlow`, stored in
  history, shared with other threads): each state must be its own object.

**Example.**

```kotlin
data class Stats(val count: Int, val sum: Long, val max: Int)

fun statsCandidate(values: IntArray): Stats {
    var count = 0
    var sum = 0L
    var max = Int.MIN_VALUE
    for (v in values) {
        count++
        sum += v
        max = maxOf(max, v)
    }
    return Stats(count, sum, max)
}
```

Runnable: `statsBaseline` / `statsCandidate` in `Representation.kt`.

**Cost removed.** One `Stats` per element. Measured (1,000 values):
baseline 32,032 B/call, candidate 32 B/call (the returned object).
Escape analysis did not remove the loop-carried copies. JMH:
`copyBaseline` 1,856 ± 96.6 ns/op, 32,032 B/op; `copyCandidate`
671.0 ± 44.2 ns/op, 32 B/op.

**Verify.**

1. `verify.sh verify representation`: `PASS data copy` and the empty
   input case (`Stats(0, 0, Int.MIN_VALUE)`).
1. `verify.sh bytecode`: `Stats.copy` in the baseline only.

## Explicit equals order for hot keys

**Definition.** A data class derives its generated `equals` from the
primary-constructor properties ([data classes][data]). `javap -c` on
`RouteKey.equals` (kotlinc 2.4.20) shows that it compares them in
declaration order and returns at the first difference. With a long
`String` first, unequal keys that share it compare the whole string
before reaching the cheap `Int`.

**Use when.**

- A profile shows a data class `equals` on hash-map keys or in
  `distinct`, and keys often share an expensive first property (paths,
  names) while differing in a cheap one (version, id).

**Do not use when.**

- You would get the order by reordering the constructor properties: that
  changes `componentN`, destructuring, and every positional call site.
  Write `equals` and `hashCode` by hand on a regular class instead, and
  keep them consistent.
- Keys already differ mostly in the first property.

**Example.**

```kotlin
class RouteKeyFast(val path: String, val version: Int) {
    override fun equals(other: Any?): Boolean =
        other is RouteKeyFast && version == other.version &&
            path == other.path

    override fun hashCode(): Int = 31 * path.hashCode() + version
}
```

Runnable: `RouteKey` (data class) and `RouteKeyFast` in
`Representation.kt`.

**Cost removed.** A full string comparison per unequal key. JMH
(`/api/` plus 1,024 characters, equal content in distinct `String`
instances): `equalsBaseline` 65.2 ± 14.4 ns/op, 0 B/op; `equalsCandidate`
1.3 ± 2.2 ns/op, 0 B/op.

**Verify.**

1. `verify.sh verify representation`: `data equals differs` and
   `data equals same` compare both classes on equal and unequal keys.
1. `BENCH_FILTER=equals sh assets/examples/verify.sh measure`.

[vc]: https://kotlinlang.org/docs/inline-classes.html
[vc-repr]: https://kotlinlang.org/docs/inline-classes.html#representation
[valueof]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Integer.html#valueOf(int)
[interop-static]: https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-fields
[interop-field]: https://kotlinlang.org/docs/java-to-kotlin-interop.html#instance-fields
[interop-static-methods]: https://kotlinlang.org/docs/java-to-kotlin-interop.html#static-methods
[data]: https://kotlinlang.org/docs/data-classes.html
[Representation.kt]: ../assets/examples/constructs/src/main/kotlin/constructs/Representation.kt
[Consts.kt]: ../assets/examples/constructs/src/main/kotlin/constructs/Consts.kt
