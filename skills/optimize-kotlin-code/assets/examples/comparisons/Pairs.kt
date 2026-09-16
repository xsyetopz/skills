// Kotlin/JVM examples. Shared-language concepts are not JVM performance promises on other backends.
object Pairs {
    fun baselineAppend(values: List<Int>): List<Int> {
        var result = emptyList<Int>()
        for (value in values) result = result + value
        return result
    }
    fun candidateAppend(values: List<Int>): List<Int> {
        val result = ArrayList<Int>(values.size)
        for (value in values) result.add(value)
        return result
    }
    fun baselineCounts(values: List<String>): Map<String, Int> =
        values.groupBy { it }.mapValues { it.value.size }
    fun candidateCounts(values: List<String>): Map<String, Int> =
        values.groupingBy { it }.eachCount()
    fun baselinePrefix(values: List<Int>, limit: Int): List<Int> =
        values.filter { it % 2 == 0 }.map { it * it }.take(limit)
    fun candidatePrefix(values: List<Int>, limit: Int): List<Int> =
        values.asSequence().filter { it % 2 == 0 }.map { it * it }.take(limit).toList()
    fun baselineJoin(values: List<String>): String = values.fold("") { a, b -> a + b }
    fun candidateJoin(values: List<String>): String = buildString {
        for (value in values) append(value)
    }
    fun baselineSum(values: IntArray): Long = values.map { it.toLong() }.sum()
    fun candidateSum(values: IntArray): Long {
        var sum = 0L
        for (value in values) sum += value.toLong()
        return sum
    }
    fun baselineLengths(values: List<String>): Map<String, Int> =
        values.associate { it to it.length }
    fun candidateLengths(values: List<String>): Map<String, Int> =
        values.associateWith { it.length }

    fun verify() {
        var checks = 0
        for (length in 0..5) {
            var possibilities = 1
            repeat(length) { possibilities *= 3 }
            for (code in 0 until possibilities) {
                var rest = code
                val values = List(length) { val next = rest % 3 - 1; rest /= 3; next }
                val before = values.toList()
                val strings = values.map { it.toString() }
                check(baselineAppend(values) == candidateAppend(values))
                check(baselineCounts(strings) == candidateCounts(strings))
                for (limit in 0..length + 1) check(baselinePrefix(values, limit) == candidatePrefix(values, limit))
                check(baselineJoin(strings) == candidateJoin(strings))
                check(baselineSum(values.toIntArray()) == candidateSum(values.toIntArray()))
                check(baselineLengths(strings) == candidateLengths(strings))
                check(values == before)
                checks += 8
            }
        }
        val unicode = listOf("é", "e\u0301", "é", "🙂", "\u0000")
        val counts = mapOf("é" to 2, "e\u0301" to 1, "🙂" to 1, "\u0000" to 1)
        check(baselineCounts(unicode) == counts && candidateCounts(unicode) == counts)
        check(baselineJoin(listOf("a", "", "é", "🙂")) == "aé🙂")
        check(candidateJoin(listOf("a", "", "é", "🙂")) == "aé🙂")
        val lengths = mapOf("é" to 1, "e\u0301" to 2, "🙂" to 2)
        check(baselineLengths(listOf("é", "e\u0301", "🙂")) == lengths)
        check(candidateLengths(listOf("é", "e\u0301", "🙂")) == lengths)
        check(baselinePrefix(listOf(1, 2, 3, 4, 6), 2) == listOf(4, 16))
        check(candidatePrefix(listOf(1, 2, 3, 4, 6), 2) == listOf(4, 16))
        check(baselineSum(intArrayOf(Int.MIN_VALUE, Int.MAX_VALUE)) == -1L)
        check(candidateSum(intArrayOf(Int.MIN_VALUE, Int.MAX_VALUE)) == -1L)
        for (fn in listOf(::baselinePrefix, ::candidatePrefix)) {
            var threw = false
            try { fn(listOf(2), -1) }
            catch (expected: IllegalArgumentException) { threw = true }
            check(threw)
        }
        // Reject eager -> lazy substitution when callback effects are observable.
        var eagerCalls = 0
        listOf(1, 2, 3).map { eagerCalls++; it }.take(1)
        var lazyCalls = 0
        listOf(1, 2, 3).asSequence().map { lazyCalls++; it }.take(1).toList()
        check(eagerCalls == 3 && lazyCalls == 1)
        println("PASS $checks differential checks + expected result and trap tests")
    }
    @JvmStatic
    fun main(args: Array<String>) {
        if (args.contentEquals(arrayOf("verify"))) { verify(); return }
        require(args.size == 3 && args[0] in listOf("baseline", "candidate")) {
            "usage: Pairs verify | baseline|candidate CASE SIZE"
        }
        val which = args[1].toInt()
        val size = args[2].toInt()
        require(size in 0..100000)
        val values = List(size) { it % 31 - 15 }
        val strings = values.map { it.toString() }
        val candidate = args[0] == "candidate"
        val result: Any = when (which) {
            1 -> if (candidate) candidateAppend(values) else baselineAppend(values)
            2 -> (if (candidate) candidateCounts(strings) else baselineCounts(strings)).toSortedMap()
            3 -> if (candidate) candidatePrefix(values, 8) else baselinePrefix(values, 8)
            4 -> if (candidate) candidateJoin(strings) else baselineJoin(strings)
            5 -> if (candidate) candidateSum(values.toIntArray()) else baselineSum(values.toIntArray())
            6 -> (if (candidate) candidateLengths(strings) else baselineLengths(strings)).toSortedMap()
            7 -> if (candidate) candidateSum(values.toIntArray()) else baselineSum(values.toIntArray())
            8 -> if (candidate) candidatePrefix(values, 8) else baselinePrefix(values, 8)
            else -> error("case 1..8")
        }
        println(result)
    }
}
