package toporders

data class Order(val id: Long, val total: Int)

/** Ids of the first [limit] orders, in list order, whose total is over 100. */
fun topIds(orders: List<Order>, limit: Int): List<Long> =
    orders.filter { it.total > 100 }.map { it.id }.take(limit)
