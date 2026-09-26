package constructs

import java.util.concurrent.{Executors, TimeUnit}
import java.util.concurrent.atomic.AtomicInteger
import scala.concurrent.{Await, ExecutionContext, Future, blocking}
import scala.concurrent.duration.*

/** Records the peak number of tasks inside `sleepy` at the same time. */
final class Gauge:
  private val running = AtomicInteger()
  private val peakSeen = AtomicInteger()
  def sleepy(ms: Long): Int =
    val now = running.incrementAndGet()
    peakSeen.accumulateAndGet(now, math.max)
    try { Thread.sleep(ms); 1 }
    finally running.decrementAndGet()
  def peak: Int = peakSeen.get

object BlockingFutures:
  def baseline(tasks: Int, g: Gauge)(using ExecutionContext): Int =
    val fs = List.fill(tasks)(Future(g.sleepy(50)))
    Await.result(Future.sequence(fs), 60.seconds).sum

  def candidate(tasks: Int, g: Gauge)(using ExecutionContext): Int =
    val fs = List.fill(tasks)(Future(blocking(g.sleepy(50))))
    Await.result(Future.sequence(fs), 60.seconds).sum

object DedicatedPool:
  def run(tasks: Int, threads: Int, g: Gauge): Int =
    val pool = Executors.newFixedThreadPool(threads)
    try
      given ExecutionContext = ExecutionContext.fromExecutor(pool)
      val fs = List.fill(tasks)(Future(g.sleepy(50)))
      Await.result(Future.sequence(fs), 60.seconds).sum
    finally
      pool.shutdown()
      pool.awaitTermination(10, TimeUnit.SECONDS)

object Parasitic:
  /** Name of the thread that ran a cheap map callback. */
  def callbackThread(ec: ExecutionContext): String =
    val done = Future.successful(41)
    val f = done.map(_ => Thread.currentThread.getName)(using ec)
    Await.result(f, 10.seconds)

object ConcurrencyChecks:
  def run(): Unit =
    import Check.*
    val global = ExecutionContext.global
    val cores = Runtime.getRuntime.availableProcessors
    val tasks = cores * 4
    val g1 = Gauge()
    equal("futures-baseline", tasks,
      BlockingFutures.baseline(tasks, g1)(using global))
    val g2 = Gauge()
    equal("futures-blocking", tasks,
      BlockingFutures.candidate(tasks, g2)(using global))
    isTrue("global without blocking stays at parallelism", g1.peak <= cores,
      s"peak ${g1.peak}, availableProcessors $cores")
    isTrue("blocking lets global exceed parallelism", g2.peak > cores,
      s"peak ${g2.peak}, availableProcessors $cores")

    val g3 = Gauge()
    equal("dedicated-pool", tasks, DedicatedPool.run(tasks, tasks, g3))
    isTrue("dedicated pool runs blocking tasks beyond the core count",
      g3.peak > cores, s"peak ${g3.peak} of $tasks, cores $cores")

    val caller = Thread.currentThread.getName
    equal("parasitic runs on the calling thread", caller,
      Parasitic.callbackThread(ExecutionContext.parasitic))
    val onGlobal = Parasitic.callbackThread(global)
    isTrue("global hops to a pool thread", onGlobal != caller,
      s"callback on $onGlobal")
