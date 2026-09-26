package billing

final case class Order(id: Long, cents: Long)

object Billing:
  /** Sum of all order amounts in cents (wraps on overflow like Long addition). */
  def total(orders: List[Order]): Long =
    var s = 0L
    var i = 0
    while i < orders.length do
      s += orders(i).cents
      i += 1
    s

  /** Number of orders at or above `threshold` cents. */
  def countLarge(orders: List[Order], threshold: Long): Int =
    var n = 0
    var i = 0
    while i < orders.length do
      if orders(i).cents >= threshold then n += 1
      i += 1
    n
