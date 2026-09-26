// Compiled twice by verify.sh diagnostics: with Scala 2.13 (@specialized
// generates Box$mcI$sp) and with Scala 3 (the annotation is ignored).
package specialized

class Box[@specialized(Int) T](val value: T) {
  def get: T = value
}

object Specialized {
  def sum(xs: Array[Box[Int]]): Long = {
    var acc = 0L
    var i = 0
    while (i < xs.length) { acc += xs(i).get; i += 1 }
    acc
  }
}
