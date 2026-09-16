//> using scala "3.3.8"
//> using jvm "21"
import java.util.concurrent.atomic.AtomicInteger

object Semantics:
  def contract(bad: Boolean, topic: Int): Boolean = topic match
    case 1 =>
      var calls = 0
      if bad then List(1,2,3).view.map { n => calls += 1; n }.take(1).toList
      else List(1,2,3).map { n => calls += 1; n }.take(1)
      calls == 3
    case 2 =>
      val source = Iterator(1,2,3)
      val first = source.toList
      val second = if bad then source.toList else first
      first == List(1,2,3) && second == first
    case 3 =>
      val source = collection.mutable.ArrayBuffer(1)
      // Seq here is immutable in Scala 3: the mutable-key variant is exercised
      // through collection.Seq explicitly instead of claiming type equivalence.
      val lookup = collection.mutable.HashMap[collection.Seq[Int],String]()
      lookup(if bad then source else source.toVector) = "value"
      source += 2
      lookup.get(Vector(1)).contains("value")
    case 4 =>
      val a=1e16; val b= -1e16; val c=1.0
      (if bad then a+(b+c) else (a+b)+c) == 1.0
    case 5 =>
      var calls=0
      val source=List(1,2).view.map { n => calls += 1; n }
      if bad then { source.toList; source.toList }
      else { val cached=source.toList; cached.toList; cached.toList }
      calls==2
    case 6 =>
      val maximum=Int.MaxValue
      try
        if bad then maximum+1 else Math.addExact(maximum,1)
        false
      catch case _: ArithmeticException => true
    case 7 =>
      val values=List(2,1,2)
      (if bad then values.toSet.toList else values)==List(2,1,2)
    case 8 =>
      val count=AtomicInteger()
      if bad then
        val a=count.get(); val b=count.get()
        count.set(a+1);count.set(b+1)
      else {count.incrementAndGet();count.incrementAndGet()}
      count.get()==2
    case _ => throw IllegalArgumentException("topic must be 1..8")
  def main(args: Array[String]): Unit =
    require(args.length==2 && Set("red","green")(args(0)),"usage: red|green TOPIC")
    val topic=args(1).toInt
    val pass=contract(args(0)=="red",topic)
    println(s"CONTRACT topic $topic: ${if pass then "PASS" else "FAIL"}")
    if !pass then sys.exit(1)
