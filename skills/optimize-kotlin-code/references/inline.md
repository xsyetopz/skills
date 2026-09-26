# Inline functions and lambdas

Removing function objects, closure boxes, and boxing at higher-order call
sites. Pairs live in
[`Inline.kt`][Inline.kt].
`verify.sh verify inline` runs the oracle and allocation checks,
`verify.sh bytecode` the `javap` assertions, and `verify.sh measure` the
JMH pairs. Local numbers are machine-specific (see
[measurement](measurement.md)). JMH rows are `Score ± Error` in ns/op with
the settings in `Benchmarks.kt` (3 x 1 s warmup, 5 x 1 s measurement,
1 fork) and `gc.alloc.rate.norm` in B/op.

Tier: Executed. `verify inline`, `noea`, `bytecode`, `benchmark`, and
`measure` ran locally for every card in this file.

## Contents

- Inline higher-order function
- Captured var in a non-inline lambda
- Reified type parameter
- noinline parameter
- crossinline parameter

## Inline higher-order function

**Definition.** `inline fun f(block: (T) -> R)` copies the body of `f`
and of the lambda argument into each call site: no function object, no
`invoke` call ([inline functions][inline]). Without `inline`, a Kotlin
lambda is an object that captures its closure, and on the JVM a
`(Int) -> Boolean` is a `Function1<Integer, Boolean>`, so every call boxes
the argument and the result.

**Use when.**

- A small higher-order function is called in a hot loop with a lambda
  literal, and `javap` shows `invokedynamic` creating a `Function1`, plus
  `Function1.invoke` with `Integer.valueOf` in the callee.
- The call site is megamorphic (the same higher-order function receives
  many different lambdas). The Kotlin docs single out "megamorphic
  call-sites inside loops" as where inlining pays off.

**Do not use when.**

- The function body is large or called from many places: inlining "may
  cause the generated code to grow" ([inline functions][inline]), which
  can push hot callers past the JIT's inlining size limits.
- The function is public API: its body is copied into client modules, so
  changing it requires recompiling clients, and it cannot use `private`
  or `internal` declarations unless they are `@PublishedApi`.
- The lambda must be stored or passed to a non-inline function: use
  `noinline` (below) or keep the function non-inline.

**Example.**

```kotlin
inline fun countIfCandidate(
    values: IntArray,
    predicate: (Int) -> Boolean,
): Int {
    var count = 0
    for (value in values) if (predicate(value)) count++
    return count
}

fun countAboveCandidate(values: IntArray, limit: Int): Int =
    countIfCandidate(values) { it > limit }
```

Runnable: `countIfBaseline` / `countIfCandidate` in `Inline.kt`.

**Cost removed.** Bytecode: the baseline call site has one
`invokedynamic` producing `Function1`, and `countIfBaseline` calls
`Integer.valueOf` and `Function1.invoke` per element. The candidate has
neither. Allocation (thread counter, 1,000 elements): **no difference**
with default flags, 0 B/call for both, because C2 inlined the small
callee and removed the lambda and the boxes. With
`-XX:-DoEscapeAnalysis` the baseline allocates 13,968 B/call and the
candidate 0 B. JMH: `inlineBaseline` 830.4 ± 1,026 ns/op, 0 B/op;
`inlineCandidate` 717.6 ± 289.3 ns/op, 0 B/op (first run 656.2 ± 49.9
vs 898.9 ± 1,918): **no difference** within error. Claim the bytecode
change; claim time only if your own measurement of the real call site
shows it.

**Verify.**

1. `sh assets/examples/verify.sh verify inline`: `PASS inline countIf`
   and the empty-array case.
1. `sh assets/examples/verify.sh bytecode`: `countAboveBaseline` has 1
   `invokedynamic`, `countAboveCandidate` has none.
1. `BENCH_FILTER=inline sh assets/examples/verify.sh measure`.

## Captured var in a non-inline lambda

**Definition.** A local `var` that a non-inline lambda modifies moves
into a heap box, `kotlin.jvm.internal.Ref$IntRef` (one class per
primitive type, `ObjectRef` for references), because the lambda object
may outlive the frame. An inline higher-order function (such as the
stdlib `forEach`) keeps the `var` in a local slot.

**Use when.**

- `javap` shows `new kotlin/jvm/internal/Ref$IntRef` in a hot function.

**Do not use when.**

- The lambda runs later or on another thread (callbacks, `Runnable`,
  coroutines): the box is what makes the shared variable work. A
  non-atomic `IntRef` shared across threads is a data race in both forms.

**Example.**

```kotlin
fun sumCapturedCandidate(values: IntArray): Int {
    var sum = 0
    values.forEach { sum += it } // stdlib forEach is inline
    return sum
}
```

Runnable: `sumCapturedBaseline` (non-inline `eachBaseline`) and
`sumCapturedCandidate` in `Inline.kt`.

**Cost removed.** One `Ref$IntRef` and one lambda object per call, plus a
field read and write per element. Thread counter: **no difference** in
bytes with default flags (0 B/call both); 13,984 B/call vs 0 B without
escape analysis. JMH: `capturedBaseline` 318.2 ± 41.6 ns/op, 0 B/op;
`capturedCandidate` 319.1 ± 14.8 ns/op, 0 B/op: **no difference**.

**Verify.**

1. `verify.sh verify inline`: `PASS captured var`.
1. `verify.sh bytecode`: `Ref\$IntRef` present in `sumCapturedBaseline`,
   absent in `sumCapturedCandidate`.

## Reified type parameter

**Definition.** `inline fun <reified T>` makes `T` available at run time
inside the inlined body. `it is T` then compiles to an `instanceof` of
the concrete class at each call site, instead of a `Class<T>` parameter
and `Class.isInstance` ([reified type parameters][inline-reified]).

**Use when.**

- An API takes `Class<T>` or `KClass<T>` only to filter or cast
  (`filterIsInstance`, JSON or DI lookups by type).

**Do not use when.**

- `T` is chosen at run time (the class comes from configuration):
  reified parameters need a type known at compile time, and non-inline
  functions cannot have them.
- Java must call the function: Java cannot call a reified inline
  function.

**Example.**

```kotlin
inline fun <reified T> countInstancesCandidate(items: List<Any>): Int =
    items.count { it is T }

fun stringsCandidate(items: List<Any>): Int =
    countInstancesCandidate<String>(items)
```

Runnable: `stringsBaseline` / `stringsCandidate` in `Inline.kt`.

**Cost removed.** Bytecode: `Class.isInstance` in the baseline,
`instanceof java/lang/String` in the candidate. Time: `reifiedBaseline`
625.9 ± 63.7 ns/op, 0 B/op; `reifiedCandidate` 637.3 ± 44.1 ns/op,
0 B/op: **no difference**. On this JDK the gain is API shape (no `Class`
argument), not speed.

**Verify.**

1. `verify.sh verify inline`: `PASS reified` and `PASS reified count`.
1. `verify.sh bytecode`: `countInstancesBaseline` has
   `Class.isInstance`; `stringsCandidate` has `instanceof` and no
   `isInstance`.

## noinline parameter

**Definition.** In an inline function, a `noinline` parameter is passed
as a real function object, so it can be stored or passed on, while the
other lambda parameters are still inlined ([noinline][inline-noinline]).

**Use when.**

- A function is non-inline only because it stores one of its lambdas
  (listeners, deferred callbacks), and its other lambdas run immediately
  in a hot path.

**Do not use when.**

- Every lambda is stored: `inline` then only adds code size. kotlinc
  2.4.20 warns "expected performance impact from inlining is
  insignificant" (checked locally).

**Example.**

```kotlin
val listeners = ArrayList<() -> Unit>()

inline fun registerCandidate(now: () -> Unit, noinline later: () -> Unit) {
    now()
    listeners.add(later)
}
```

Runnable: `useRegisterBaseline` / `useRegisterCandidate` in `Inline.kt`.

**Cost removed.** One function object per call: the baseline call site
has 2 `invokedynamic` instructions, the candidate 1.

**Verify.**

1. `verify.sh verify inline`: `PASS noinline order` (immediate lambdas
   run before stored ones, identical output).
1. `verify.sh bytecode`: `useRegisterBaseline` 2 and
   `useRegisterCandidate` 1 `invokedynamic`.

## crossinline parameter

**Definition.** `crossinline` marks a lambda parameter of an inline
function that is called from another execution context, such as an
`object` or nested lambda. The lambda may not use a non-local `return`
([crossinline][inline-crossinline]). The compiler generates one class per
call site with the lambda body inlined into it.

**Use when.**

- An inline function wraps its lambda in a `Runnable`, `Comparator`, or
  other object, and the call site creates one per call.

**Do not use when.**

- The lambda needs a non-local `return` from the caller: `crossinline`
  forbids it.
- There are many call sites: each gets its own generated class
  (`...$inlined$...`), which adds class-loading and metaspace cost.

**Example.**

```kotlin
inline fun deferCandidate(crossinline body: () -> Unit): Runnable =
    Runnable { body() }

fun useDeferCandidate(log: StringBuilder, id: Int): Runnable =
    deferCandidate { log.append(id) }
```

Runnable: `useDeferBaseline` / `useDeferCandidate` in `Inline.kt`.

**Cost removed.** One object per call: the baseline allocates a
`Function0` and a `Runnable` wrapping it, the candidate one generated
`Runnable`. Thread counter, default flags: 40 B/call vs 24 B/call.

**Verify.**

1. `verify.sh verify inline`: `PASS crossinline deferred` (nothing runs
   until `run()`) and `PASS crossinline ran`.
1. `verify.sh verify inline`: `PASS alloc crossinline`; `verify.sh
   bytecode`: no `invokedynamic` and one `new ...inlined...` in
   `useDeferCandidate`.

[inline]: https://kotlinlang.org/docs/inline-functions.html
[inline-reified]: https://kotlinlang.org/docs/inline-functions.html#reified-type-parameters
[inline-noinline]: https://kotlinlang.org/docs/inline-functions.html#noinline
[inline-crossinline]: https://kotlinlang.org/docs/inline-functions.html#non-local-jump-expressions
[Inline.kt]: ../assets/examples/constructs/src/main/kotlin/constructs/Inline.kt
