package bench

import java.util.concurrent.TimeUnit
import org.openjdk.jmh.annotations.*
import scala.collection.immutable.ArraySeq
import constructs.*

/** JMH pairs for the constructs. Inputs are built in @Setup, outside the
  * measured method; every result is returned so JMH consumes it.
  */
@State(Scope.Benchmark)
@BenchmarkMode(Array(Mode.AverageTime))
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
class Pairs:
  var list: List[Int] = Nil
  var arraySeq: ArraySeq[Int] = ArraySeq.empty
  var vector: Vector[Int] = Vector.empty
  var array: Array[Int] = Array.emptyIntArray
  var longs: Array[Long] = Array.emptyLongArray
  var words: Array[String] = Array.empty
  var shapes: Array[Shape] = Array.empty
  var config: Config = Config(7)
  var bigVector: Vector[Long] = Vector.empty

  @Setup def setup(): Unit =
    list = List.tabulate(1000)(i => i * 1000 - 7)
    arraySeq = list.to(ArraySeq)
    vector = list.toVector
    array = list.toArray
    longs = Array.tabulate(1000)(i => i * 1000L)
    words = Array.tabulate(5000)(i => s"w${i % 50}")
    shapes = Array.tabulate(300)(i =>
      if i % 3 == 0 then Circle(i) else if i % 3 == 1 then Square(i)
      else Rect(i, 2))
    bigVector = Vector.tabulate(2000000)(_.toLong)

  @Benchmark def indexedList: Long = IndexedAccess.baseline(list)
  @Benchmark def indexedArraySeq: Long = IndexedAccess.candidate(arraySeq)
  @Benchmark def indexedVector: Long = IndexedAccess.candidate(vector)

  @Benchmark def strictChain: Int = StrictChain.baseline(list)
  @Benchmark def iteratorChain: Int = StrictChain.candidate(list)

  @Benchmark def viewStrict: Vector[Int] = ViewChain.baseline(vector)
  @Benchmark def viewLazy: Vector[Int] = ViewChain.candidate(vector)

  @Benchmark def arrayMapSum: Int = ArrayLoop.baseline(array)
  @Benchmark def arrayWhile: Int = ArrayLoop.candidate(array)

  @Benchmark def genericSum: Long = GenericBoxing.baseline(longs)
  @Benchmark def primitiveSum: Long = GenericBoxing.candidate(longs)

  @Benchmark def countImmutable: AnyRef = WordCount.immutableMap(words)
  @Benchmark def countMutable: AnyRef = WordCount.mutableHashMap(words)
  @Benchmark def countJava: AnyRef = WordCount.javaHashMap(words)

  @Benchmark def lazyInLoop: Long = LazyHoist.baseline(config, array)
  @Benchmark def lazyHoisted: Long = LazyHoist.candidate(config, array)
  @Benchmark def lazyThreadUnsafe: Long =
    LazyHoist.threadUnsafe(config, array)

  @Benchmark def sealedMatch: Double = SealedMatch.total(shapes)

  @Benchmark def switchIfChain: Int =
    var acc = 0
    var i = 0
    while i < array.length do
      acc += Switch.baseline(i & 7); i += 1
    acc

  @Benchmark def switchTable: Int =
    var acc = 0
    var i = 0
    while i < array.length do
      acc += Switch.candidate(i & 7); i += 1
    acc

  @Benchmark def interpolateF: String =
    Interpolation.formattedPlain(123456, "name")
  @Benchmark def interpolateS: String = Interpolation.plain(123456, "name")

  @Benchmark def sequentialSum: Long = ParallelSum.baseline(bigVector)
  @Benchmark def parallelSum: Long = ParallelSum.candidate(bigVector)
