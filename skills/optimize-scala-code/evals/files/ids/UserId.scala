package ids

final case class UserId(value: Long) extends AnyVal

object UserIds:
  def load(n: Int): Array[UserId] = Array.tabulate(n)(i => UserId(i.toLong * 31))
  def maxId(ids: Array[UserId]): UserId = ids.maxBy(_.value)
  def lookup(id: UserId): String = s"user:${id.value}"
