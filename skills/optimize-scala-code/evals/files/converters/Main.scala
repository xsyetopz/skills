package converters

@main def demo(): Unit =
  val m = new java.util.HashMap[String, Integer]()
  m.put("b", 2); m.put("a", 1)
  println(Registry.names(m))
  println(Registry.totals(java.util.List.of(1, 2, 3)))
  println(Registry.toJava(Seq("x", "y")))
