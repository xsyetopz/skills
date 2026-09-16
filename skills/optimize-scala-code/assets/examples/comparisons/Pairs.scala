//> using scala "3.3.8"
//> using jvm "21"
//> using options "-deprecation" "-feature" "-unchecked" "-Werror"
import scala.collection.mutable.ListBuffer

object Pairs {
  def baselineAppend(values: List[Int]): List[Int] = {
    var result = List.empty[Int]
    values.foreach(value => result = result :+ value)
    result
  }
  def candidateAppend(values: List[Int]): List[Int] = {
    val result = ListBuffer.empty[Int]
    values.foreach(value => result += value)
    result.toList
  }
  def baselineIndexedSum(values: List[Int]): Long = {
    var result = 0L
    var i = 0
    val size = values.length
    while (i < size) { result += values(i).toLong; i += 1 }
    result
  }
  def candidateIndexedSum(values: List[Int]): Long = {
    var result = 0L
    val iterator = values.iterator
    while (iterator.hasNext) result += iterator.next().toLong
    result
  }
  def baselineCounts(values: List[String]): Map[String, Int] =
    values.groupBy(identity).view.mapValues(_.size).toMap
  def candidateCounts(values: List[String]): Map[String, Int] =
    values.groupMapReduce(identity)(_ => 1)(_ + _)
  def baselineSum(values: List[Int]): Long =
    values.filter(_ % 2 == 0).map(value => value.toLong * value).sum
  def candidateSum(values: List[Int]): Long =
    values.iterator.filter(_ % 2 == 0).map(value => value.toLong * value).sum
  def baselineJoin(values: List[String]): String = values.foldLeft("")(_ + _)
  def candidateJoin(values: List[String]): String = {
    val result = new StringBuilder
    values.foreach(value => result.append(value))
    result.toString
  }
  def baselineMembership(values: List[String], queries: List[String]): List[Boolean] =
    queries.map(values.contains)
  def candidateMembership(values: List[String], queries: List[String]): List[Boolean] = {
    val members = values.toSet
    queries.map(members.contains)
  }
  def baselineBoxedNumericSum(values: List[java.lang.Integer]): Long =
    values.iterator.map(_.longValue).sum
  def candidatePrimitiveNumericSum(values: Array[Int]): Long = {
    var result = 0L
    var index = 0
    while (index < values.length) { result += values(index); index += 1 }
    result
  }
  def baselineStrictPipeline(values: List[Int]): List[Long] =
    values.filter(_ % 2 == 0).map(value => value.toLong * value)
  def candidateViewPipeline(values: List[Int]): List[Long] =
    values.view.filter(_ % 2 == 0).map(value => value.toLong * value).toList
  def verify(): Unit = {
    var checks = 0
    for (length <- 0 to 5; code <- 0 until math.pow(3, length).toInt) {
      var rest = code
      val values = List.fill(length) { val value = rest % 3 - 1; rest /= 3; value }
      val strings = values.map(_.toString)
      require(baselineAppend(values) == candidateAppend(values))
      require(baselineIndexedSum(values) == candidateIndexedSum(values))
      require(baselineCounts(strings) == candidateCounts(strings))
      require(baselineSum(values) == candidateSum(values))
      require(baselineJoin(strings) == candidateJoin(strings))
      require(baselineMembership(strings, List("0", "9")) == candidateMembership(strings, List("0", "9")))
      require(baselineBoxedNumericSum(values.map(Int.box)) == candidatePrimitiveNumericSum(values.toArray))
      require(baselineStrictPipeline(values) == candidateViewPipeline(values))
      checks += 8
    }
    val texts = List("é", "e\u0301", "é", "🙂", "\u0000")
    val expected = Map("é" -> 2, "e\u0301" -> 1, "🙂" -> 1, "\u0000" -> 1)
    require(baselineCounts(texts) == expected && candidateCounts(texts) == expected)
    require(baselineAppend(List(2, 1, 2)) == List(2, 1, 2))
    require(candidateAppend(List(2, 1, 2)) == List(2, 1, 2))
    require(baselineIndexedSum(List(Int.MinValue, Int.MaxValue)) == -1L)
    require(candidateIndexedSum(List(Int.MinValue, Int.MaxValue)) == -1L)
    require(baselineSum(List(-3, 2, 2, 0, 5)) == 8L)
    require(candidateSum(List(-3, 2, 2, 0, 5)) == 8L)
    require(baselineJoin(List("a", "", "é", "🙂")) == "aé🙂")
    require(candidateJoin(List("a", "", "é", "🙂")) == "aé🙂")
    require(baselineMembership(List("a", "a"), List("a", "b")) == List(true, false))
    require(candidateMembership(List("a", "a"), List("a", "b")) == List(true, false))
    var effects = 0
    val delayed = List(1, 2, 3).view.map { value => effects += 1; value }
    require(effects == 0)
    delayed.toList
    require(effects == 3)
    delayed.toList
    require(effects == 6) // Views are lazy, not a memoized result cache.
    println(s"PASS $checks differential checks + expected result and trap tests")
  }
  def main(args: Array[String]): Unit = {
    if (args.toList == List("verify")) { verify(); return }
    require(args.length == 3 && Set("baseline", "candidate").contains(args(0)),
      "usage: Pairs verify | baseline|candidate CASE SIZE")
    val which = args(1).toInt
    val size = args(2).toInt
    require(size >= 0 && size <= 100000)
    val values = List.tabulate(size)(i => i % 31 - 15)
    val strings = values.map(_.toString)
    val candidate = args(0) == "candidate"
    val result: Any = which match {
      case 1 => if (candidate) candidateAppend(values) else baselineAppend(values)
      case 2 => if (candidate) candidateIndexedSum(values) else baselineIndexedSum(values)
      case 3 => (if (candidate) candidateCounts(strings) else baselineCounts(strings)).toList.sortBy(_._1)
      case 4 => if (candidate) candidateSum(values) else baselineSum(values)
      case 5 => if (candidate) candidateJoin(strings) else baselineJoin(strings)
      case 6 => if (candidate) candidateMembership(strings, strings) else baselineMembership(strings, strings)
      case 7 => if (candidate) candidatePrimitiveNumericSum(values.toArray)
        else baselineBoxedNumericSum(values.map(Int.box))
      case 8 => if (candidate) candidateViewPipeline(values)
        else baselineStrictPipeline(values)
      case _ => throw new IllegalArgumentException("case 1..8")
    }
    println(result)
  }
}
