package constructs

/** Runs every equivalence and allocation oracle; exits 1 on failure. */
@main def verify(): Unit =
  println(s"java ${System.getProperty("java.version")}, " +
    s"scala-library ${scala.util.Properties.versionNumberString}")
  Check.selfTest()
  CollectionChecks.run()
  LanguageChecks.run()
  ConcurrencyChecks.run()
  Check.finish()

/** A hot loop for JFR: rebuilds an immutable Map per batch for `seconds`. */
@main def profile(seconds: Int): Unit =
  val words = Array.tabulate(5000)(i => s"w${i % 50}")
  val end = System.nanoTime + seconds * 1_000_000_000L
  var batches = 0L
  while System.nanoTime < end do
    Check.sinkRef = WordCount.immutableMap(words)
    batches += 1
  println(s"profile: $batches batches")
