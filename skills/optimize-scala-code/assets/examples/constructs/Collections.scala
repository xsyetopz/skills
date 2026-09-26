package constructs

import scala.collection.immutable.ArraySeq
import scala.collection.mutable
import scala.collection.parallel.CollectionConverters.*

/** Collection constructs: each object holds a baseline and a candidate. */
object IndexedAccess:
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

object Footprint:
  def baseline(n: Int): List[Int] = List.tabulate(n)(i => i * 1000)
  def candidate(n: Int): ArraySeq[Int] =
    ArraySeq.tabulate(n)(i => i * 1000) // ArraySeq.ofInt over Array[Int]

object UpdateAt:
  def baseline(xs: List[Int], i: Int): List[Int] =
    xs.updated(i, -1) // L: copies the i cells before index i

  def candidate(xs: Vector[Int], i: Int): Vector[Int] =
    xs.updated(i, -1) // eC: copies one path of the vector's tree

object BufferGrowth:
  def baseline(n: Int): mutable.ArrayBuffer[Int] =
    val b = mutable.ArrayBuffer.empty[Int] // grows by copying
    var i = 0
    while i < n do { b += i * 1000; i += 1 }
    b

  def candidate(n: Int): mutable.ArrayBuffer[Int] =
    val b = mutable.ArrayBuffer.empty[Int]
    b.sizeHint(n) // capacity n before the first append
    var i = 0
    while i < n do { b += i * 1000; i += 1 }
    b

  def primitive(n: Int): Array[Int] =
    val b = Array.newBuilder[Int] // int[] storage: no boxes
    b.sizeHint(n)
    var i = 0
    while i < n do { b += i * 1000; i += 1 }
    b.result()

object ListAppend:
  def baseline(xs: List[Int]): List[Int] =
    var out = List.empty[Int]
    for x <- xs do out = out :+ x // copies `out` every time
    out

  def candidate(xs: List[Int]): List[Int] =
    val out = mutable.ListBuffer.empty[Int]
    for x <- xs do out += x
    out.toList // no copy: ListBuffer hands over its cells

object StrictChain:
  def baseline(xs: List[Int]): Int =
    xs.filter(_ % 3 == 0).map(_ * 2).length

  def candidate(xs: List[Int]): Int =
    xs.iterator.filter(_ % 3 == 0).map(_ * 2).length

object ViewChain:
  def baseline(xs: Vector[Int]): Vector[Int] =
    xs.map(_ + 1).filter(_ % 2 == 0).map(_ * 3)

  def candidate(xs: Vector[Int]): Vector[Int] =
    xs.view.map(_ + 1).filter(_ % 2 == 0).map(_ * 3).toVector

  /** Returns how often `f` ran when a view is consumed twice. */
  def reevaluations(): Int =
    var calls = 0
    val v = Vector(1, 2, 3).view.map { x => calls += 1; x }
    v.toList
    v.toList
    calls

object ArrayLoop:
  def baseline(xs: Array[Int]): Int = xs.map(_ + 1).sum

  def candidate(xs: Array[Int]): Int =
    var sum = 0
    var i = 0
    while i < xs.length do { sum += xs(i) + 1; i += 1 }
    sum

object SizedBuilder:
  def baseline(n: Int): Array[Int] =
    val b = Array.newBuilder[Int]
    var i = 0
    while i < n do { b += i; i += 1 }
    b.result()

  def candidate(n: Int): Array[Int] =
    val b = Array.newBuilder[Int]
    b.sizeHint(n) // exact capacity: no regrowth, result() returns it
    var i = 0
    while i < n do { b += i; i += 1 }
    b.result()

object StringJoin:
  def baseline(parts: List[String]): String = parts.foldLeft("")(_ + _)

  def candidate(parts: List[String]): String =
    val sb = new java.lang.StringBuilder(parts.foldLeft(0)(_ + _.length))
    parts.foreach(sb.append)
    sb.toString

object WordCount:
  def immutableMap(words: Array[String]): Map[String, Int] =
    words.foldLeft(Map.empty[String, Int]) { (m, w) =>
      m.updated(w, m.getOrElse(w, 0) + 1)
    }

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

  def javaHashMap(words: Array[String])
      : java.util.HashMap[String, Integer] =
    val m = new java.util.HashMap[String, Integer]()
    val one: Integer = 1
    var i = 0
    while i < words.length do
      m.merge(words(i), one, (a, b) => a + b)
      i += 1
    m

  /** Counts into an Array[Int] indexed through a key-to-slot map. */
  def slotCounts(words: Array[String]): Map[String, Int] =
    val slot = mutable.HashMap.empty[String, Int]
    val counts = new Array[Int](words.length)
    var i = 0
    while i < words.length do
      counts(slot.getOrElseUpdate(words(i), slot.size)) += 1
      i += 1
    slot.iterator.map((w, s) => w -> counts(s)).toMap

object GroupCount:
  def baseline(xs: List[String]): Map[String, Int] =
    xs.groupBy(identity).view.mapValues(_.size).toMap

  def candidate(xs: List[String]): Map[String, Int] =
    xs.groupMapReduce(identity)(_ => 1)(_ + _)

/** A key that counts equals calls, so lookup work is observable. */
final class CountedKey(val id: Int):
  override def equals(other: Any): Boolean =
    CountedKey.comparisons += 1
    other match
      case k: CountedKey => k.id == id
      case _             => false
  override def hashCode: Int = id

object CountedKey:
  var comparisons = 0L

object Membership:
  def baseline(members: List[CountedKey], qs: Array[CountedKey]): Int =
    qs.count(members.contains)

  def candidate(members: List[CountedKey], qs: Array[CountedKey]): Int =
    val set = members.toSet
    qs.count(set.contains)

object ParallelSum:
  def baseline(xs: Vector[Long]): Long = xs.map(x => x * x % 7).sum

  def candidate(xs: Vector[Long]): Long = xs.par.map(x => x * x % 7).sum

object CollectionChecks:
  def run(): Unit =
    import Check.*
    val ints = List.tabulate(2000)(i => i * 1000 - 7)
    equal("indexed-access", IndexedAccess.baseline(ints),
      IndexedAccess.candidate(ints.to(ArraySeq)))
    equal("indexed-access-vector", IndexedAccess.baseline(ints),
      IndexedAccess.candidate(ints.toVector))
    equal("indexed-access-empty", IndexedAccess.baseline(Nil),
      IndexedAccess.candidate(ArraySeq.empty[Int]))

    equal("footprint", Footprint.baseline(1000), Footprint.candidate(1000))
    fewerBytes("footprint",
      bytesPerOp(() => Footprint.baseline(1000)),
      bytesPerOp(() => Footprint.candidate(1000)), 0.25)

    val vec1000 = ints.take(1000).toVector
    val list1000 = ints.take(1000)
    equal("update-at", UpdateAt.baseline(list1000, 900),
      UpdateAt.candidate(vec1000, 900).toList)
    fewerBytes("update-at",
      bytesPerOp(() => UpdateAt.baseline(list1000, 900)),
      bytesPerOp(() => UpdateAt.candidate(vec1000, 900)), 0.1)

    equal("buffer-presized", BufferGrowth.baseline(1000),
      BufferGrowth.candidate(1000))
    equal("buffer-primitive", BufferGrowth.baseline(1000).toSeq,
      BufferGrowth.primitive(1000).toSeq)
    val grown = bytesPerOp(() => BufferGrowth.baseline(1000))
    val presized = bytesPerOp(() => BufferGrowth.candidate(1000))
    val prim = bytesPerOp(() => BufferGrowth.primitive(1000))
    fewerBytes("buffer-presized", grown, presized, 0.95)
    fewerBytes("buffer-primitive", presized, prim, 0.5)

    val small = ints.take(200)
    equal("list-append", ListAppend.baseline(small),
      ListAppend.candidate(small))
    equal("list-append-empty", ListAppend.baseline(Nil),
      ListAppend.candidate(Nil))
    fewerBytes("list-append",
      bytesPerOp(() => ListAppend.baseline(small), 2000, 200),
      bytesPerOp(() => ListAppend.candidate(small)), 0.05)

    equal("strict-chain", StrictChain.baseline(ints),
      StrictChain.candidate(ints))
    fewerBytes("strict-chain",
      bytesPerOpLong(() => StrictChain.baseline(ints).toLong),
      bytesPerOpLong(() => StrictChain.candidate(ints).toLong), 0.05)

    val vec = ints.toVector
    equal("view-chain", ViewChain.baseline(vec), ViewChain.candidate(vec))
    fewerBytes("view-chain",
      bytesPerOp(() => ViewChain.baseline(vec)),
      bytesPerOp(() => ViewChain.candidate(vec)), 0.9)
    equal("view-reevaluates", 6, ViewChain.reevaluations())

    val arr = ints.toArray
    equal("array-loop", ArrayLoop.baseline(arr), ArrayLoop.candidate(arr))
    equal("array-loop-overflow", ArrayLoop.baseline(Array(Int.MaxValue)),
      ArrayLoop.candidate(Array(Int.MaxValue)))
    fewerBytes("array-loop",
      bytesPerOpLong(() => ArrayLoop.baseline(arr).toLong),
      bytesPerOpLong(() => ArrayLoop.candidate(arr).toLong), 0.0)

    equal("sized-builder", SizedBuilder.baseline(1000).toSeq,
      SizedBuilder.candidate(1000).toSeq)
    fewerBytes("sized-builder",
      bytesPerOp(() => SizedBuilder.baseline(1000)),
      bytesPerOp(() => SizedBuilder.candidate(1000)), 0.5)

    val parts = List.tabulate(300)(i => s"part$i;")
    equal("string-join", StringJoin.baseline(parts),
      StringJoin.candidate(parts))
    equal("string-join-empty", StringJoin.baseline(Nil),
      StringJoin.candidate(Nil))
    fewerBytes("string-join",
      bytesPerOp(() => StringJoin.baseline(parts), 2000, 200),
      bytesPerOp(() => StringJoin.candidate(parts)), 0.05)

    val words = Array.tabulate(5000)(i => s"w${i % 50}")
    val expected = WordCount.immutableMap(words)
    equal("wordcount-mutable", expected,
      WordCount.mutableHashMap(words).toMap)
    equal("wordcount-java", expected, {
      val m = WordCount.javaHashMap(words)
      m.keySet.toArray(Array.empty[String])
        .map(k => k -> m.get(k).intValue).toMap
    })
    equal("wordcount-slots", expected, WordCount.slotCounts(words))
    val imm = bytesPerOp(() => WordCount.immutableMap(words), 2000, 200)
    val mut = bytesPerOp(() => WordCount.mutableHashMap(words), 2000, 200)
    val jhm = bytesPerOp(() => WordCount.javaHashMap(words), 2000, 200)
    val slots = bytesPerOp(() => WordCount.slotCounts(words), 2000, 200)
    fewerBytes("wordcount-mutable", imm, mut, 0.5)
    fewerBytes("wordcount-java", imm, jhm, 0.5)
    fewerBytes("wordcount-slots", mut, slots, 0.5)

    val names = List.tabulate(3000)(i => s"k${i % 40}")
    equal("group-count", GroupCount.baseline(names),
      GroupCount.candidate(names))
    val grouped = bytesPerOp(() => GroupCount.baseline(names), 500, 100)
    val reduced = bytesPerOp(() => GroupCount.candidate(names), 500, 100)
    println(f"INFO group-count groupBy $grouped%.0f B/op, " +
      f"groupMapReduce $reduced%.0f B/op")

    val members = List.tabulate(500)(CountedKey(_))
    val queries = Array.tabulate(500)(i => CountedKey(i * 2))
    CountedKey.comparisons = 0
    val found = Membership.baseline(members, queries)
    val linear = CountedKey.comparisons
    CountedKey.comparisons = 0
    equal("membership", found, Membership.candidate(members, queries))
    val hashed = CountedKey.comparisons
    isTrue("membership equals calls", hashed * 20 < linear,
      s"List.contains $linear equals calls, Set.contains $hashed")

    val longs = Vector.tabulate(200000)(_.toLong)
    equal("parallel-sum", ParallelSum.baseline(longs),
      ParallelSum.candidate(longs))
    // Parallel reduction regroups operations: exact for Long, not Double.
    val (a, b, c) = (1e16, -1e16, 1.0)
    isTrue("double addition is not associative", (a + b) + c != a + (b + c),
      s"${(a + b) + c} vs ${a + (b + c)}")

    val once = Iterator(1, 2, 3)
    val first = once.toList
    equal("iterator is one-shot", (List(1, 2, 3), Nil), (first, once.toList))
    equal("toSet drops duplicates", List(2, 1), List(2, 1, 2).toSet.toList)
