package converters

import scala.collection.JavaConverters._

object Registry:
  def names(m: java.util.Map[String, Integer]): List[String] =
    m.keySet.asScala.toList.sorted

  def totals(xs: java.util.List[Integer]): Int =
    xs.asScala.map(_.intValue).sum

  def toJava(xs: Seq[String]): java.util.List[String] =
    xs.asJava
