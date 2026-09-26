package metrics

object Stats:
  /** Generic sum, part of the library's public API (also used with Double and BigDecimal). */
  def sum[T](xs: Array[T])(using n: Numeric[T]): T =
    xs.foldLeft(n.zero)(n.plus)
