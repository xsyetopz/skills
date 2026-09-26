package constructs

import scala.annotation.{switch, tailrec, threadUnsafe}

/** Language and representation constructs. */
object GenericBoxing:
  def baseline[T](xs: Array[T])(using n: Numeric[T]): T =
    var acc = n.zero
    var i = 0
    while i < xs.length do { acc = n.plus(acc, xs(i)); i += 1 }
    acc

  inline def inlined[T](xs: Array[T])(using n: Numeric[T]): T =
    var acc = n.zero
    var i = 0
    while i < xs.length do { acc = n.plus(acc, xs(i)); i += 1 }
    acc

  /** Expands `inlined` with T = Long: calls LongIsIntegral.plus(JJ)J. */
  def inlinedLong(xs: Array[Long]): Long = inlined(xs)

  def candidate(xs: Array[Long]): Long =
    var acc = 0L
    var i = 0
    while i < xs.length do { acc += xs(i); i += 1 }
    acc

/** A user-defined generic function trait: not specialized. */
trait Fn[A, B]:
  def apply(a: A): B

object FunctionSpecialization:
  val plainInc: Fn[Int, Int] = x => x + 1000
  val scalaInc: Int => Int = x => x + 1000

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

/** Value class: erased to Double in signatures, boxed in arrays. */
final class MetersVC(val value: Double) extends AnyVal

object ValueClassArray:
  def baseline(n: Int): Array[MetersVC] =
    val out = new Array[MetersVC](n) // one MetersVC object per element
    var i = 0
    while i < n do { out(i) = MetersVC(i * 1.5); i += 1 }
    out

  def candidate(n: Int): Array[Units.Meters] = Units.opaqueArray(n)

  def addVC(a: MetersVC, b: MetersVC): MetersVC =
    MetersVC(a.value + b.value) // signature takes and returns double

  def boxedByGeneric(xs: Array[Double]): List[MetersVC] =
    xs.iterator.map(MetersVC(_)).toList // type argument: allocates

object Logging:
  var enabled = false
  var lines = 0

  def byValue(msg: String): Unit = if enabled then lines += 1

  def byName(msg: => String): Unit = if enabled then { msg; lines += 1 }

  inline def inlined(inline msg: String): Unit =
    if enabled then { msg; lines += 1 }

  def baseline(id: Long): Long = { byValue(s"id=$id"); id }
  def byNameCall(id: Long): Long = { byName(s"id=$id"); id }
  def candidate(id: Long): Long = { inlined(s"id=$id"); id }

object TailRec:
  def baseline(n: Int): Long = if n == 0 then 0L else n + baseline(n - 1)

  def candidate(n: Int): Long =
    @tailrec def loop(i: Int, acc: Long): Long =
      if i == 0 then acc else loop(i - 1, acc + i)
    loop(n, 0L)

object Switch:
  def candidate(op: Int): Int = (op: @switch) match
    case 0 => 10
    case 1 => 20
    case 2 => 30
    case 3 => 40
    case _ => -1

  def baseline(op: Int): Int =
    if op == 0 then 10
    else if op == 1 then 20
    else if op == 2 then 30
    else if op == 3 then 40
    else -1

sealed trait Shape
final case class Circle(r: Double) extends Shape
final case class Square(s: Double) extends Shape
final case class Rect(w: Double, h: Double) extends Shape

object SealedMatch:
  def area(s: Shape): Double = s match // instanceof tests in case order
    case Circle(r)  => 3.0 * r * r
    case Square(a)  => a * a
    case Rect(w, h) => w * h

  def total(xs: Array[Shape]): Double =
    var acc = 0.0
    var i = 0
    while i < xs.length do { acc += area(xs(i)); i += 1 }
    acc

final class Config(seed: Int):
  lazy val factor: Int = seed * 3
  @threadUnsafe lazy val unsafeFactor: Int = seed * 3

object LazyHoist:
  def baseline(c: Config, xs: Array[Int]): Long =
    var acc = 0L
    var i = 0
    while i < xs.length do { acc += xs(i) * c.factor; i += 1 }
    acc

  def candidate(c: Config, xs: Array[Int]): Long =
    val f = c.factor // one lazy-val read outside the loop
    var acc = 0L
    var i = 0
    while i < xs.length do { acc += xs(i) * f; i += 1 }
    acc

  def threadUnsafe(c: Config, xs: Array[Int]): Long =
    var acc = 0L
    var i = 0
    while i < xs.length do { acc += xs(i) * c.unsafeFactor; i += 1 }
    acc

object Enrich:
  implicit class RichLong(val x: Long):
    def squaredPlus(y: Long): Long = x * x + y

  implicit class RichLongVC(val x: Long) extends AnyVal:
    def squaredPlusVC(y: Long): Long = x * x + y

  extension (x: Long) def squaredPlusExt(y: Long): Long = x * x + y

  def baseline(x: Long): Long = x.squaredPlus(1)
  def valueClass(x: Long): Long = x.squaredPlusVC(1)
  def candidate(x: Long): Long = x.squaredPlusExt(1)

object ArrayAsSeq:
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

  def baseline(xs: Array[Int]): Long =
    sumSeq(scala.collection.immutable.ArraySeq.unsafeWrapArray(xs))

  def candidate(xs: IArray[Int]): Long = sumIArray(xs)

object Interpolation:
  def formatted(id: Int, score: Double): String = f"$id%d:$score%.2f"
  def plain(id: Int, name: String): String = s"$id:$name"
  def formattedPlain(id: Int, name: String): String = f"$id%d:$name%s"

object LanguageChecks:
  def run(): Unit =
    import Check.*
    val longs = Array.tabulate(1000)(i => i * 1000L)
    equal("generic-boxing", GenericBoxing.baseline(longs),
      GenericBoxing.candidate(longs))
    equal("generic-boxing-inline", GenericBoxing.inlinedLong(longs),
      GenericBoxing.candidate(longs))
    val generic = bytesPerOpLong(() => GenericBoxing.baseline(longs))
    val inl = bytesPerOpLong(() => GenericBoxing.inlinedLong(longs))
    val prim = bytesPerOpLong(() => GenericBoxing.candidate(longs))
    fewerBytes("generic-boxing", generic, prim, 0.0)
    fewerBytes("generic-boxing-inline", generic, inl, 0.0)

    val ints = Array.tabulate(1000)(i => i * 1000)
    equal("function-specialization",
      FunctionSpecialization.baseline(ints, FunctionSpecialization.plainInc),
      FunctionSpecialization.candidate(ints, FunctionSpecialization.scalaInc))
    val fnMono = bytesPerOpLong(() => FunctionSpecialization
      .baseline(ints, FunctionSpecialization.plainInc))
    val scalaMono = bytesPerOpLong(() => FunctionSpecialization
      .candidate(ints, FunctionSpecialization.scalaInc))
    println(f"INFO monomorphic Fn $fnMono%.1f B/op, " +
      f"Int => Int $scalaMono%.1f B/op")
    // Three implementations make the f(x) call site megamorphic, so C2
    // cannot inline it and cannot remove the box.
    val fns = Array[Fn[Int, Int]](_ + 1000, _ + 2000, _ + 3000)
    val sfs = Array[Int => Int](_ + 1000, _ + 2000, _ + 3000)
    var k = 0
    while k < 30000 do
      FunctionSpecialization.baseline(ints, fns(k % 3))
      FunctionSpecialization.candidate(ints, sfs(k % 3))
      k += 1
    fewerBytes("function-specialization megamorphic",
      bytesPerOpLong(() => FunctionSpecialization.baseline(ints, fns(0))),
      bytesPerOpLong(() => FunctionSpecialization.candidate(ints, sfs(0))),
      0.0)

    equal("opaque-array", ValueClassArray.baseline(100).map(_.value).toSeq,
      ValueClassArray.candidate(100).map(_.value).toSeq)
    fewerBytes("opaque-array",
      bytesPerOp(() => ValueClassArray.baseline(1000)),
      bytesPerOp(() => ValueClassArray.candidate(1000)), 0.5)
    val m = ValueClassArray.addVC(MetersVC(1.5), MetersVC(2.0))
    equal("value-class-add", 3.5, m.value)
    val ds = Array.tabulate(100)(_ * 1.5)
    val vcAdd = bytesPerOpLong(() =>
      ValueClassArray.addVC(MetersVC(ds(3)), MetersVC(ds(4))).value.toLong)
    isTrue("value-class-signature allocation", vcAdd < 1.0,
      f"addVC $vcAdd%.1f B/op")
    val vcList = bytesPerOp(() => ValueClassArray.boxedByGeneric(ds))
    isTrue("value-class-generic allocation", vcList > 100 * 16.0,
      f"List[MetersVC] of 100: $vcList%.1f B/op")

    Logging.enabled = false
    val byValue = bytesPerOpLong(() => Logging.baseline(123456L))
    val byName = bytesPerOpLong(() => Logging.byNameCall(123456L))
    val inlined = bytesPerOpLong(() => Logging.candidate(123456L))
    fewerBytes("inline-parameter", byValue, inlined, 0.0)
    println(f"INFO by-name disabled log: $byName%.1f B/op")
    Logging.enabled = true
    Logging.lines = 0
    Logging.baseline(1); Logging.byNameCall(1); Logging.candidate(1)
    equal("logging-enabled-lines", 3, Logging.lines)
    Logging.enabled = false

    equal("tailrec", TailRec.baseline(1000), TailRec.candidate(1000))
    val deep =
      try Right(TailRec.baseline(1_000_000))
      catch case _: StackOverflowError => Left("StackOverflowError")
    equal("tailrec-baseline-deep", Left("StackOverflowError"), deep)
    equal("tailrec-candidate-deep", 500000500000L,
      TailRec.candidate(1_000_000))

    equal("switch", (-2 to 5).map(Switch.baseline),
      (-2 to 5).map(Switch.candidate))

    val shapes: Array[Shape] =
      Array.tabulate(300)(i => (i % 3: @switch) match
        case 0 => Circle(i)
        case 1 => Square(i)
        case _ => Rect(i, 2))
    isTrue("sealed-match allocation",
      bytesPerOpLong(() => SealedMatch.total(shapes).toLong) < 1.0,
      "unapply of final case classes does not allocate")

    val c = Config(7)
    equal("lazy-hoist", LazyHoist.baseline(c, ints),
      LazyHoist.candidate(c, ints))
    equal("lazy-thread-unsafe", LazyHoist.baseline(c, ints),
      LazyHoist.threadUnsafe(c, ints))

    equal("extension", Enrich.baseline(12345L), Enrich.candidate(12345L))
    equal("extension-vc", Enrich.baseline(12345L), Enrich.valueClass(12345L))
    val rich = bytesPerOpLong(() => Enrich.baseline(12345L))
    val ext = bytesPerOpLong(() => Enrich.candidate(12345L))
    println(f"INFO implicit class $rich%.1f B/op, extension $ext%.1f B/op")

    equal("iarray", ArrayAsSeq.baseline(ints),
      ArrayAsSeq.candidate(IArray.unsafeFromArray(ints)))
    val iarr = IArray.unsafeFromArray(ints)
    val wrapped = bytesPerOpLong(() => ArrayAsSeq.baseline(ints))
    val direct = bytesPerOpLong(() => ArrayAsSeq.candidate(iarr))
    // Measured equal (C2 removes the wrapper and the boxes); the bytecode
    // difference is asserted by `verify.sh diagnostics`.
    println(f"INFO Seq over Array $wrapped%.1f B/op, IArray $direct%.1f B/op")

    equal("interpolation-number", Interpolation.formatted(7, 1.005),
      "7:1.01")
    equal("interpolation-plain", Interpolation.formattedPlain(7, "a"),
      Interpolation.plain(7, "a"))
    fewerBytes("interpolation",
      bytesPerOp(() => Interpolation.formattedPlain(123456, "name")),
      bytesPerOp(() => Interpolation.plain(123456, "name")), 0.5)
