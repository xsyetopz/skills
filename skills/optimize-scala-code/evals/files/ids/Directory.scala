package ids

/** Holds every known user id in memory (tens of millions in production). */
final class Directory(val ids: Array[UserId]):
  def contains(id: UserId): Boolean = ids.contains(id)
  def describe(i: Int): String = UserIds.lookup(ids(i))
