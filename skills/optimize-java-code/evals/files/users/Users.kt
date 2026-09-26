package users

data class UserId(val raw: Long)

class UserDirectory(private val names: Map<UserId, String>) {
    fun nameOf(id: UserId): String? = names[id]

    fun idsWithPrefix(prefix: String): List<UserId> =
        names.filter { it.value.startsWith(prefix) }.keys.sortedBy { it.raw }
}

fun main() {
    val directory = UserDirectory(mapOf(UserId(3) to "ann", UserId(1) to "andy", UserId(2) to "bob"))
    println(directory.idsWithPrefix("an").map { it.raw })
    println(directory.nameOf(UserId(2)))
}
