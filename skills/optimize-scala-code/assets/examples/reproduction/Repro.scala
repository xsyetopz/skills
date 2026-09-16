//> using scala "3.3.8"
//> using jvm "21"

object Repro:
  def main(args: Array[String]): Unit =
    var calls = 0
    val view = List(1, 2, 3).view.map { value => calls += 1; value }
    val actual = view.take(1).toList
    println(s"actual=$actual calls=$calls")
    println("expected eager callback count=3")
    assert(calls == 1)
