package constructs

import java.lang.management.ManagementFactory

/** A non-generic operation: calling it never boxes the result. */
trait LongOp:
  def run(): Long

/** Equivalence and allocation oracle shared by every construct. */
object Check:
  private val threads = ManagementFactory.getThreadMXBean
    .asInstanceOf[com.sun.management.ThreadMXBean]
  private var failures = 0
  @volatile var sinkRef: AnyRef = null
  @volatile var sinkLong: Long = 0L

  def equal[A](name: String, expected: A, actual: A): Unit =
    if expected != actual then
      failures += 1
      println(s"FAIL $name: expected $expected, got $actual")
    else println(s"PASS $name")

  def isTrue(name: String, condition: Boolean, detail: => String): Unit =
    if condition then println(s"PASS $name ($detail)")
    else
      failures += 1
      println(s"FAIL $name ($detail)")

  /** Bytes allocated by this thread per call of `op`, after `warm` calls
    * so the measured calls run C2-compiled code.
    */
  def bytesPerOp(op: () => AnyRef, warm: Int = 20000, reps: Int = 2000)
      : Double =
    var i = 0
    while i < warm do { sinkRef = op(); i += 1 }
    val before = threads.getCurrentThreadAllocatedBytes()
    i = 0
    while i < reps do { sinkRef = op(); i += 1 }
    (threads.getCurrentThreadAllocatedBytes() - before).toDouble / reps

  /** Same as [[bytesPerOp]] for primitive results. `LongOp` rather than
    * `() => Long`: a Scala 3 lambda typed `() => Long` may box its result.
    */
  def bytesPerOpLong(op: LongOp, warm: Int = 20000, reps: Int = 2000)
      : Double =
    var i = 0
    while i < warm do { sinkLong = op.run(); i += 1 }
    val before = threads.getCurrentThreadAllocatedBytes()
    i = 0
    while i < reps do { sinkLong = op.run(); i += 1 }
    (threads.getCurrentThreadAllocatedBytes() - before).toDouble / reps

  /** Prints baseline and candidate bytes/op and asserts the candidate
    * allocates at most `ratio` times the baseline.
    */
  def fewerBytes(name: String, baseline: Double, candidate: Double,
      ratio: Double): Unit =
    isTrue(s"$name allocation", candidate <= baseline * ratio,
      f"baseline $baseline%.1f B/op, candidate $candidate%.1f B/op")

  def selfTest(): Unit =
    val noop = bytesPerOpLong(() => 42L)
    isTrue("harness self-test", noop < 1.0, f"no-op $noop%.2f B/op")

  def finish(): Unit =
    if failures > 0 then
      println(s"$failures check(s) failed")
      sys.exit(1)
    println("ALL CHECKS PASSED")
