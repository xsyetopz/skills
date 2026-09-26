# Language and representation constructs

Each card changes how Scala represents or compiles a construct: boxing,
wrappers, closures, dispatch, initialization, and formatting. Examples are
in `assets/examples/constructs/Language.scala`; `LanguageChecks` proves
equivalence and allocation, and `verify.sh diagnostics` asserts the
bytecode shape with `javap`.

Tier: executed locally (`verify.sh verify`, `diagnostics`, `benchmark`,
`measure`); the Scala 2.13 `@specialized` example is compiled only.
Measured on: Apple M1 Max, macOS arm64, OpenJDK 25.0.4.1, Scala 3.8.4,
scala-cli 1.16.0. B/op values come from the ThreadMXBean oracle after
20,000 warm-up calls (C2-compiled code). Bytecode facts are for Scala
3.8.4 unless a card says Scala 2.13. Bytecode and JIT statements do not
transfer to Scala.js or Scala Native.

## Contents

- Primitive overload instead of a generic Numeric method
- Inline def for a generic numeric helper
- @specialized (Scala 2.13 only)
- Function1 specialization instead of a custom generic SAM
- Opaque type instead of a value class for arrays
- Value class (extends AnyVal)
- Inline parameter for a disabled log message
- By-name parameter for a disabled log message
- @tailrec loop instead of non-tail recursion
- @switch on an Int match
- Sealed trait match
- Hoist a lazy val read out of a loop
- @threadUnsafe lazy val
- Extension method instead of an implicit class
- Implicit class extending AnyVal
- IArray instead of a Seq view of an Array
- s interpolator instead of f for plain values

## Primitive overload instead of a generic Numeric method

**Definition.** A method with a type parameter `T` erases `T` to
`Object`; `Numeric[T].plus` is then called as
`plus(Object, Object): Object`, so every element and partial result is
boxed. A monomorphic overload on `Array[Long]` uses `long` arithmetic.

**Use when.**

- `allocation-by-class` or `-prof gc` shows `java.lang.Long`,
  `Integer`, or `Double` from a generic numeric helper.
- The hot call sites use one or two concrete element types.

**Do not use when.**

- The generic method is cold: a duplicate adds maintenance for no
  measured gain.
- Overflow semantics would change: keep the same width (`Long` stays
  `Long`) or use `Math.addExact` if the generic version threw.

**Example.**

```scala
def baseline[T](xs: Array[T])(using n: Numeric[T]): T =
  var acc = n.zero
  var i = 0
  while i < xs.length do { acc = n.plus(acc, xs(i)); i += 1 }
  acc

def candidate(xs: Array[Long]): Long =
  var acc = 0L
  var i = 0
  while i < xs.length do { acc += xs(i); i += 1 }
  acc
```

Runnable: `GenericBoxing` in `Language.scala`.

**Cost removed.** Measured, 1,000 longs: 23,976 B/op versus 0 B/op.
JMH: `genericSum` 3,390 ± 1,767 ns/op, `primitiveSum` 319 ± 13 ns/op.

**Verify.**

1. `PASS generic-boxing`.
1. `PASS generic-boxing allocation (...)`; `verify.sh diagnostics` asserts
   `Numeric.plus:(Ljava/lang/Object;Ljava/lang/Object;)` in the baseline.

## Inline def for a generic numeric helper

**Definition.** An `inline def` is expanded at each call site during
type checking ([inline][inline]). With `T = Long` known at the call site,
`n.plus` resolves to `Numeric.LongIsIntegral.plus(long, long): long`, so
the loop no longer boxes. On dropping `@specialized`, the Scala 3
migration guide says "Similar benefits can be derived from `inline`
declarations" ([dropped features][dropped]).

**Use when.**

- A small generic helper is hot at a few call sites with concrete
  types.

**Do not use when.**

- The helper is large or called from many sites: every call site gets a
  copy (bytecode size, JIT inlining budget).
- The call site itself is generic in `T`: the expansion then still sees
  an abstract `Numeric[T]` and boxes.
- The helper is recursive: inline expansion depth is limited (32 by
  default, `-Xmax-inlines`) ([inline][inline]).

**Example.**

```scala
inline def inlined[T](xs: Array[T])(using n: Numeric[T]): T =
  var acc = n.zero
  var i = 0
  while i < xs.length do { acc = n.plus(acc, xs(i)); i += 1 }
  acc

def inlinedLong(xs: Array[Long]): Long = inlined(xs)
```

Runnable: `GenericBoxing.inlinedLong` in `Language.scala`.

**Cost removed.** Measured: 23,976 B/op (generic) versus 0 B/op (inline
at a `Long` call site).

**Verify.**

1. `PASS generic-boxing-inline`.
1. `verify.sh diagnostics`: `PASS inline def resolves plus to (JJ)J`
   (`LongIsIntegral$.plus:(JJ)J` in `inlinedLong`).

## @specialized (Scala 2.13 only)

**Definition.** In Scala 2, `@specialized(Int)` on a type parameter
makes the compiler emit extra classes and methods for the listed
primitive types (for `class Box[@specialized(Int) T]`, a subclass
`Box$mcI$sp`). The Scala 3 migration guide states: "The `@specialized`
annotation from Scala 2 is ignored in Scala 3" ([dropped features][dropped]).

**Use when.**

- The code is compiled with Scala 2.13 and a generic class is hot with
  primitive arguments.

**Do not use when.**

- The code is compiled with Scala 3: the annotation compiles and does
  nothing. Use a monomorphic overload or `inline` (cards above).
- Many type parameters are specialized: classes multiply per
  combination (code size).
- The class is a value class: value classes "may not have `@specialized`
  type parameters" ([value classes][value-classes]).

**Example.**

```scala
class Box[@specialized(Int) T](val value: T) {
  def get: T = value
}
```

Runnable: `assets/examples/scala2/Specialized.scala`, compiled by
`verify.sh diagnostics` with `--scala 2.13.18` and with `--scala 3.8.4`.

**Cost removed.** In 2.13, boxing through the generic accessor. Not
measured: tier Compiled, and the check only proves the specialized class
exists. Only the 2.13 output contains `Box$mcI$sp.class`; the Scala 3
output does not. JDK 25 needs Scala 2.13.17 or later
([JDK compatibility][jdk-compat]).

**Verify.**

1. `verify.sh diagnostics`: `PASS Scala 2.13 @specialized generates
   Box$mcI$sp`.
1. Measure allocation with `-prof gc` under Scala 2.13 (not bundled).

## Function1 specialization instead of a custom generic SAM

**Definition.** Scala 3 specializes `Function1` for primitive argument
and result types: a call `f(x)` with `f: Int => Int` compiles to
`apply$mcII$sp(I)I` ([SpecializeFunctions][specialize-functions]; the
migration guide mentions "limited support for specialized `Function`
and `Tuple`" ([dropped features][dropped])). A user-defined
`trait Fn[A, B]` erases to `apply(Object): Object`.

**Use when.**

- A hot loop calls a function value on primitives through a custom
  generic SAM trait.

**Do not use when.**

- The call site is monomorphic and C2 inlines it: with one `Fn`
  implementation, both forms measured 0 B/op because escape analysis
  removed the boxes. The difference appears only when the call site sees
  several implementations.

**Example.**

```scala
trait Fn[A, B]:
  def apply(a: A): B

def baseline(xs: Array[Int], f: Fn[Int, Int]): Long =
  var acc = 0L
  var i = 0
  while i < xs.length do { acc += f(xs(i)); i += 1 }
  acc

def candidate(xs: Array[Int], f: Int => Int): Long =
  var acc = 0L
  var i = 0
  while i < xs.length do { acc += f(xs(i)); i += 1 } // apply$mcII$sp
  acc
```

Runnable: `FunctionSpecialization` in `Language.scala`.

**Cost removed.** Measured, 1,000 ints, call site made megamorphic with
three implementations: 31,984 B/op versus 0 B/op. Monomorphic: 0 versus
0.

**Verify.**

1. `PASS function-specialization`.
1. `PASS function-specialization megamorphic allocation (...)`;
   `verify.sh diagnostics` asserts `Function1.apply$mcII$sp:(I)I` in the
   candidate and `boxToInteger` in the baseline.

## Opaque type instead of a value class for arrays

**Definition.** An opaque type alias is its underlying type at run time;
the reference states opaque types provide "type abstraction without any
overhead" ([opaque types][opaques]). `Array[Meters]` with
`opaque type Meters = Double` is a `double[]`.

**Use when.**

- Hot code stores a wrapper type around a primitive in arrays or generic
  collections.
- Signatures need a distinct type without run-time cost.

**Do not use when.**

- The code needs run-time type tests (`case m: Meters`): at run time an
  opaque type is indistinguishable from its underlying type.
- The code relies on a distinct `equals`/`toString`: they are the
  underlying type's.
- The code must compile with Scala 2 (opaque types are Scala 3 only).

**Example.**

```scala
object Units:
  opaque type Meters = Double
  object Meters:
    def apply(d: Double): Meters = d
  extension (m: Meters) def value: Double = m

  def opaqueArray(n: Int): Array[Meters] =
    val out = new Array[Meters](n) // a double[] at runtime
    var i = 0
    while i < n do { out(i) = Meters(i * 1.5); i += 1 }
    out
```

Runnable: `Units` and `ValueClassArray` in `Language.scala`.

**Cost removed.** Measured, 1,000 elements: 28,016 B/op for
`Array[MetersVC]` (a reference array plus one object per element) versus
8,016 B/op for `Array[Meters]` (one `double[]`).

**Verify.**

1. `PASS opaque-array` (same values).
1. `PASS opaque-array allocation (...)`; `verify.sh diagnostics`:
   `PASS opaque Array[Meters] is double[]` (descriptor `(I)[D`).

## Value class (extends AnyVal)

**Definition.** `final class MetersVC(val value: Double) extends AnyVal`
is erased to `double` in method signatures. The overview lists when an
instance is allocated: when it "is treated as another type", "is
assigned to an array", or used in "runtime type tests, such as pattern
matching" ([value classes][value-classes]).

**Use when.**

- A wrapper appears only in method parameters, results, and local values.
- The code must also compile with Scala 2.

**Do not use when.**

- Instances go into arrays, generic collections, or pattern matches: they
  allocate; use an opaque type (card above) under Scala 3.
- The class needs more than one field, `val`/`lazy val` members, or
  custom `equals` (value-class restrictions in the overview).

**Example.**

```scala
final class MetersVC(val value: Double) extends AnyVal

def addVC(a: MetersVC, b: MetersVC): MetersVC =
  MetersVC(a.value + b.value) // signature takes and returns double

def boxedByGeneric(xs: Array[Double]): List[MetersVC] =
  xs.iterator.map(MetersVC(_)).toList // type argument: allocates
```

Runnable: `ValueClassArray` in `Language.scala`.

**Cost removed.** Measured: `addVC` 0 B/op; `List[MetersVC]` of 100
elements 7,256 B/op (one object per element plus list cells).

**Verify.**

1. `PASS value-class-add`, `PASS value-class-signature allocation`.
1. `verify.sh diagnostics`: `PASS value class parameters erase to
   double` (`(DD)D`) and `PASS value class array holds objects`.

## Inline parameter for a disabled log message

**Definition.** An `inline` parameter of an `inline def` is substituted
into the body at each use instead of evaluated at the call; the
reference contrasts this with by-name parameters ([inline][inline]). A
message argument is therefore built only inside the `if enabled`
branch. This is the default; a by-name parameter (next card) is the
fallback where inline is unavailable.

**Use when.**

- A hot path calls a logging, assertion, or tracing helper whose message
  is expensive and usually discarded.

**Do not use when.**

- The parameter is used more than once in the body: each use evaluates
  it again (duplicate side effects and cost). Bind it to a local `val`
  first.
- The helper is part of a binary API used from Java or older Scala
  versions: `inline` methods expand at compile time only.

**Example.**

```scala
def byValue(msg: String): Unit = if enabled then lines += 1

inline def inlined(inline msg: String): Unit =
  if enabled then { msg; lines += 1 }

def baseline(id: Long): Long = { byValue(s"id=$id"); id }
def candidate(id: Long): Long = { inlined(s"id=$id"); id }
```

Runnable: `Logging` in `Language.scala`.

**Cost removed.** Measured, logging disabled: by-value 56 B/op, inline
0 B/op.

**Verify.**

1. `PASS logging-enabled-lines` (with logging on, each form logs once).
1. `PASS inline-parameter allocation (...)`; `verify.sh diagnostics`
   asserts `makeConcatWithConstants` in the by-value caller, an `ifeq`
   before it in the inline caller, and no call to a log method.

## By-name parameter for a disabled log message

**Definition.** A by-name parameter `msg: => String` is passed as a
`Function0` that the callee evaluates on demand. The argument is built
only if the callee evaluates it, but the call site creates the closure
object when it captures values.

**Use when.**

- `inline` is not available: Scala 2.13, or the method must remain a
  normal (virtual or Java-callable) method.

**Do not use when.**

- The hot path needs zero allocation: the disabled by-name call measured
  24 B/op (the captured `Function0`), versus 0 B/op for inline.

**Example.**

```scala
def byName(msg: => String): Unit = if enabled then { msg; lines += 1 }
def byNameCall(id: Long): Long = { byName(s"id=$id"); id }
```

Runnable: `Logging.byNameCall` in `Language.scala`.

**Cost removed.** Measured: 56 B/op (by-value) versus 24 B/op
(by-name).

**Verify.**

1. `PASS logging-enabled-lines`.
1. `INFO by-name disabled log: 24.0 B/op`; `verify.sh diagnostics`:
   `PASS by-name allocates a Function0`.

## @tailrec loop instead of non-tail recursion

**Definition.** A self-recursive call in tail position compiles to a
jump; `@tailrec` makes the compiler reject the method when it cannot
([tailrec][tailrec]).

**Use when.**

- Recursion depth grows with input size (lists, counters), so a
  `StackOverflowError` is possible.

**Do not use when.**

- The recursion is not in tail position (`n + f(n - 1)`) and has no
  accumulator yet: the annotation alone fails compilation with
  "Cannot rewrite recursive call: it is not in tail position". Add an
  accumulator parameter first.
- The recursion is mutual between methods: `@tailrec` covers only
  self-calls.

**Example.**

```scala
def baseline(n: Int): Long = if n == 0 then 0L else n + baseline(n - 1)

def candidate(n: Int): Long =
  @tailrec def loop(i: Int, acc: Long): Long =
    if i == 0 then acc else loop(i - 1, acc + i)
  loop(n, 0L)
```

Runnable: `TailRec` in `Language.scala`; the rejected form is
`assets/examples/negative/TailrecNotTail.scala`.

**Cost removed.** Stack depth. Measured: the baseline throws
`StackOverflowError` at n = 1,000,000; the candidate returns
500000500000.

**Verify.**

1. `PASS tailrec`, `PASS tailrec-baseline-deep`,
   `PASS tailrec-candidate-deep`.
1. `verify.sh diagnostics`: `PASS @tailrec loop is a goto` and
   `PASS non-tail @tailrec is rejected`.

## @switch on an Int match

**Definition.** `(x: @switch) match` asks the compiler to verify that a
match on literals compiles to a JVM `tableswitch` or `lookupswitch` and
to warn (E115) otherwise ([switch][switch], [E115][e115]).

**Use when.**

- A hot match on `Int`, `Char`, `Byte`, or `Short` literals has three or
  more cases.

**Do not use when.**

- The warning would serve as proof: Scala 3.8.4 warned only for a
  `Long` scrutinee. A match with a guard, a match on a non-`final` `val`,
  a `String` match, and a two-case match all compiled to `if` chains
  without a warning (the switch scaladoc says one- or two-case matches
  never warn). Check `javap -c` for `tableswitch`/`lookupswitch`.
- The scrutinee is `Long`, `String`, or an object: the JVM has no switch
  for it.

**Example.**

```scala
def candidate(op: Int): Int = (op: @switch) match
  case 0 => 10
  case 1 => 20
  case 2 => 30
  case 3 => 40
  case _ => -1
```

Runnable: `Switch` in `Language.scala`; the rejected `Long` form is
`assets/examples/negative/SwitchNotSwitchable.scala`.

**Cost removed.** In bytecode, a chain of compare-and-branch
instructions becomes one indexed jump. At run time, none measured: JMH
over 1,000 calls (inputs cycling 0 to 7) gave `switchTable`
1,441 ± 781 versus `switchIfChain` 604 ± 33 ns/op in run 1 and
1,142 ± 122 versus 768 ± 213 ns/op in run 2, so the `if` chain was
faster. The cause was not investigated. Treat `@switch` as a
compile-time check, not a speedup, unless your JMH run shows one.

**Verify.**

1. `PASS switch` (all inputs -2 to 5 agree with the `if` chain).
1. `verify.sh diagnostics`: `PASS @switch emits tableswitch`,
   `PASS Long @switch is rejected under -Werror`.

## Sealed trait match

**Definition.** A match on a sealed hierarchy of final case classes
compiles to `instanceof` tests in case order followed by field reads;
`unapply` on a case class returns the instance itself, so no tuple or
`Option` is allocated.

**Use when.**

- A closed set of types needs exhaustivity checking: the compiler warns
  when a case is missing.

**Do not use when.**

- The expectation is a jump table: the match runs one `instanceof` test
  per case until one succeeds. Put the most frequent case first only if
  a profile shows the match itself is hot.
- Extractors are custom `unapply` methods returning `Option`: those may
  allocate per call.

**Example.**

```scala
def area(s: Shape): Double = s match // instanceof tests in case order
  case Circle(r)  => 3.0 * r * r
  case Square(a)  => a * a
  case Rect(w, h) => w * h
```

Runnable: `SealedMatch` in `Language.scala`.

**Cost removed.** None: the check proves the match does not allocate
(measured below 1 B/op over 300 shapes). The bundled JMH `sealedMatch`
has no alternative to compare with and makes no timing claim.

**Verify.**

1. `PASS sealed-match allocation`.
1. `verify.sh diagnostics`: `PASS sealed match is an instanceof chain`
   (3 `instanceof` for 3 cases).

## Hoist a lazy val read out of a loop

**Definition.** In Scala 3.8.4, `lazy val factor: Int` compiles to a
`private volatile Object factor$lzy1` field and an accessor that reads
the field, tests `instanceof Integer`, and unboxes, calling
`factor$lzyINIT1()` (CAS through a `VarHandle`) on first use
([LazyVals phase][lazyvals-src]). The reference page describes an older
bitmap-and-`LazyVals.CAS` scheme ([lazy vals][lazy-ref]); the bytecode
matches the compiler source, not the page.

**Use when.**

- A hot loop reads the same lazy val on every iteration.

**Do not use when.**

- The loop may run zero times and the lazy val can throw: reading it
  before the loop changes when the exception is thrown. Guard the
  hoisted read with the loop's condition.

**Example.**

```scala
def candidate(c: Config, xs: Array[Int]): Long =
  val f = c.factor // one lazy-val read outside the loop
  var acc = 0L
  var i = 0
  while i < xs.length do { acc += xs(i) * f; i += 1 }
  acc
```

Runnable: `LazyHoist` in `Language.scala`.

**Cost removed.** One volatile read, type test, and unbox per
iteration. JMH, 1,000 elements: run 1 `lazyInLoop` 779 ± 22 and
`lazyHoisted` 685 ± 21 ns/op; run 2 775 ± 18 and 778 ± 172 ns/op
(inconclusive). The effect is small at most; measure before keeping
it.

**Verify.**

1. `PASS lazy-hoist`.
1. `verify.sh diagnostics`: `PASS lazy val Int is a volatile Object
   field`; JMH `lazyInLoop` versus `lazyHoisted`.

## @threadUnsafe lazy val

**Definition.** `@threadUnsafe` on a lazy val makes Scala 3 use "a faster
mechanism which is not thread-safe" ([threadUnsafe][thread-unsafe]):
in the bytecode, a plain `int` field plus a `boolean` flag, with no
volatile access and no boxing.

**Use when.**

- The object is confined to one thread (or safely published after
  initialization) and the lazy val is read in hot code.

**Do not use when.**

- Two threads may perform the first read concurrently: the initializer
  can run twice, and a thread can see a partially published value.
- The code targets Scala 2 (the annotation is Scala 3).

**Example.**

```scala
final class Config(seed: Int):
  lazy val factor: Int = seed * 3
  @threadUnsafe lazy val unsafeFactor: Int = seed * 3
```

Runnable: `Config` and `LazyHoist.threadUnsafe` in `Language.scala`.

**Cost removed.** Volatile read and unboxing per access. JMH, 1,000
elements: `lazyThreadUnsafe` 699 ± 31 and 702 ± 19 ns/op versus
`lazyInLoop` 779 ± 22 and 775 ± 18 ns/op in two runs.

**Verify.**

1. `PASS lazy-thread-unsafe`.
1. `verify.sh diagnostics`: `PASS @threadUnsafe lazy val is a plain int
   field`.

## Extension method instead of an implicit class

**Definition.** A Scala 3 extension method "translates to a specially
labelled method that takes the leading parameter section as its first
argument list" ([extension methods][extensions]): no wrapper object.
An `implicit class RichLong(val x: Long)` creates a `RichLong` per call.

**Use when.**

- Scala 3 code adds methods to a type through an `implicit class` in a
  hot path.

**Do not use when.**

- The enrichment must compile with Scala 2: use an implicit class that
  extends `AnyVal` (next card).

**Example.**

```scala
implicit class RichLong(val x: Long):
  def squaredPlus(y: Long): Long = x * x + y

extension (x: Long) def squaredPlusExt(y: Long): Long = x * x + y
```

Runnable: `Enrich` in `Language.scala`.

**Cost removed.** Measured: implicit class 24 B/op (escape analysis did
not remove the wrapper), extension 0 B/op.

**Verify.**

1. `PASS extension`.
1. `INFO implicit class 24.0 B/op, extension 0.0 B/op`;
   `verify.sh diagnostics`: `PASS implicit class wraps the receiver`,
   `PASS extension method takes the receiver as a long`.

## Implicit class extending AnyVal

**Definition.** Combining an implicit class with a value class gives
"allocation-free extension methods" ([value classes][value-classes]);
calls compile to a static-like `squaredPlusVC$extension(long, long)`.

**Use when.**

- Cross-built Scala 2.13 and Scala 3 code needs enrichment without
  allocation.

**Do not use when.**

- The class has fields besides the wrapped value or is nested in a class
  (value-class restrictions).

**Example.**

```scala
implicit class RichLongVC(val x: Long) extends AnyVal:
  def squaredPlusVC(y: Long): Long = x * x + y
```

Runnable: `Enrich.valueClass` in `Language.scala`.

**Cost removed.** The per-call wrapper of a plain implicit class.

**Verify.**

1. `PASS extension-vc`.
1. `javap -c -p` of `Enrich$` shows
   `RichLongVC$.squaredPlusVC$extension:(JJ)J`.

## IArray instead of a Seq view of an Array

**Definition.** `IArray[Int]` is an opaque immutable view of
`Array[Int]`; its `apply` compiles to `IArray$.apply([II)I`
([IArray][iarray]). Passing an `Array[Int]` as `Seq[Int]` wraps it in an
`ArraySeq` whose `apply` returns `Object` through the `Seq` interface.

**Use when.**

- An API takes `Seq[Int]` only to accept arrays immutably, and a
  profile shows `Integer` allocation or `ArraySeq` wrappers from that
  path.

**Do not use when.**

- The goal is a measurable allocation win: both measured 0 B/op (C2
  removed the wrapper and the boxes). The bytecode differs; the run-time
  allocation did not in this test.
- Callers pass `List` or `Vector`: `IArray` would force a copy.

**Example.**

```scala
def sumSeq(xs: Seq[Int]): Long =
  var acc = 0L
  var i = 0
  while i < xs.length do { acc += xs(i); i += 1 }
  acc

def sumIArray(xs: IArray[Int]): Long =
  var acc = 0L
  var i = 0
  while i < xs.length do { acc += xs(i); i += 1 }
  acc
```

Runnable: `ArrayAsSeq` in `Language.scala`.

**Cost removed.** None measured. The bytecode loses the interface call
returning `Object` and `unboxToInt`.

**Verify.**

1. `PASS iarray`; read the `INFO Seq over Array` line.
1. `verify.sh diagnostics`: `PASS Seq.apply returns a boxed element`,
   `PASS IArray.apply returns int`.

## s interpolator instead of f for plain values

**Definition.** Scala 3 rewrites `s"..."` and `raw"..."` to string
concatenation ([StringInterpolatorOpt][interp-opt]); on JDK 9+ targets
this compiled to one `invokedynamic makeConcatWithConstants`.
`f"..."` boxes its arguments and calls `StringOps.format`, which uses
`java.util.Formatter` with the default locale ([string
interpolation][interp-book], [Formatter][formatter]).

**Use when.**

- `f"$x%d"` or `f"$s%s"` formats plain integers or strings without width,
  precision, or padding in hot code.

**Do not use when.**

- The format has precision, width, or padding (`%.2f`, `%05d`): `s`
  cannot express it. Keep `f` or format explicitly.
- `f` stays and output must be locale-independent: `Formatter` uses the
  default locale, so `%.2f` can print a comma decimal separator.

**Example.**

```scala
def plain(id: Int, name: String): String = s"$id:$name"
def formattedPlain(id: Int, name: String): String = f"$id%d:$name%s"
```

Runnable: `Interpolation` in `Language.scala`.

**Cost removed.** Oracle: `f` 576 B/op versus `s` 56 B/op (the result
string only). JMH: `interpolateF` 106.3 ± 7.8 ns/op and 472 B/op;
`interpolateS` 7.3 ± 1.2 ns/op and 56 B/op.

**Verify.**

1. `PASS interpolation-plain` (same string).
1. `PASS interpolation allocation (...)`; `verify.sh diagnostics`:
   `PASS s interpolator is invokedynamic concat`,
   `PASS f interpolator calls format`.

[inline]: https://docs.scala-lang.org/scala3/reference/metaprogramming/inline.html
[dropped]: https://docs.scala-lang.org/scala3/guides/migration/incompat-dropped-features.html#specialized
[jdk-compat]: https://docs.scala-lang.org/overviews/jdk-compatibility/overview.html
[specialize-functions]: https://github.com/scala/scala3/blob/main/compiler/src/dotty/tools/dotc/transform/SpecializeFunctions.scala
[opaques]: https://docs.scala-lang.org/scala3/reference/other-new-features/opaques.html
[value-classes]: https://docs.scala-lang.org/overviews/core/value-classes.html
[tailrec]: https://www.scala-lang.org/api/3.x/scala/annotation/tailrec.html
[switch]: https://www.scala-lang.org/api/3.x/scala/annotation/switch.html
[e115]: https://docs.scala-lang.org/scala3/reference/error-codes/E115.html
[lazyvals-src]: https://github.com/scala/scala3/blob/main/compiler/src/dotty/tools/dotc/transform/LazyVals.scala
[lazy-ref]: https://docs.scala-lang.org/scala3/reference/changed-features/lazy-vals-init.html
[thread-unsafe]: https://www.scala-lang.org/api/3.x/scala/annotation/threadUnsafe.html
[extensions]: https://docs.scala-lang.org/scala3/reference/contextual/extension-methods.html
[iarray]: https://www.scala-lang.org/api/3.x/scala/IArray$.html
[interp-opt]: https://github.com/scala/scala3/blob/main/compiler/src/dotty/tools/dotc/transform/localopt/StringInterpolatorOpt.scala
[interp-book]: https://docs.scala-lang.org/scala3/book/string-interpolation.html
[formatter]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Formatter.html
