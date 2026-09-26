package users

import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.ConcurrentLinkedQueue

final case class User(id: Long, name: String)

/** Stand-in for the JDBC DAO: each load blocks its thread for ~50 ms on the database. */
object Dao:
  val inFlight = AtomicInteger(0)
  val maxInFlight = AtomicInteger(0)
  val threadNames = ConcurrentLinkedQueue[String]()

  def load(id: Long): User =
    val now = inFlight.incrementAndGet()
    maxInFlight.accumulateAndGet(now, math.max)
    threadNames.add(Thread.currentThread().getName)
    try
      Thread.sleep(50)
      if id < 0 then throw IllegalArgumentException(s"bad id $id")
      User(id, s"user-$id")
    finally inFlight.decrementAndGet()
