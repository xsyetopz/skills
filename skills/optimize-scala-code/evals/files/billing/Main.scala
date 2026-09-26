package billing

// Stand-in for the service: the JSON decoder hands us a List[Order].
@main def runBilling(n: Int = 50000): Unit =
  val orders = List.tabulate(n)(i => Order(i.toLong, (i * 37L) % 10000))
  val t0 = System.nanoTime()
  val total = Billing.total(orders)
  val large = Billing.countLarge(orders, 5000)
  val ms = (System.nanoTime() - t0) / 1e6
  println(s"total=$total large=$large (${ms} ms)")
