package constructs

import constructs.Harness.Expect

// Card: Sequence for a multi-step chain that stops early.
fun firstSquaresBaseline(values: List<Int>, limit: Int): List<Int> =
    values.filter { it % 2 == 0 }.map { it * it }.take(limit)

fun firstSquaresCandidate(values: List<Int>, limit: Int): List<Int> =
    values.asSequence().filter { it % 2 == 0 }.map { it * it }
        .take(limit).toList()

// Card: Iterable for short chains consumed completely.
fun smallChainIterable(values: List<Int>): Int =
    values.filter { it > 0 }.map { it * 2 }.sum()

fun smallChainSequence(values: List<Int>): Int =
    values.asSequence().filter { it > 0 }.map { it * 2 }.sum()

// Card: sumOf instead of map { }.sum().
fun totalLengthBaseline(words: List<String>): Int =
    words.map { it.length }.sum()

fun totalLengthCandidate(words: List<String>): Int =
    words.sumOf { it.length }

// Card: materialize a Sequence that is consumed more than once.
fun sequenceTwiceBaseline(source: () -> Int): Pair<Int, Int> {
    val values = generateSequence(1) { it + 1 }.take(4).map { it + source() }
    return values.sum() to values.count()
}

fun sequenceTwiceCandidate(source: () -> Int): Pair<Int, Int> {
    val values =
        generateSequence(1) { it + 1 }.take(4).map { it + source() }.toList()
    return values.sum() to values.size
}

// Card: buildList with capacity instead of list + element.
fun appendBaseline(values: IntArray): List<Int> {
    var result = emptyList<Int>()
    for (value in values) result = result + value
    return result
}

fun appendCandidate(values: IntArray): List<Int> =
    buildList(values.size) { for (value in values) add(value) }

// Card: buildString instead of += in a loop.
fun joinBaseline(parts: List<String>): String {
    var out = ""
    for (part in parts) out += "$part;"
    return out
}

fun joinCandidate(parts: List<String>): String =
    buildString(parts.sumOf { it.length + 1 }) {
        for (part in parts) append(part).append(';')
    }

// Card: string templates (compile to invokedynamic concat on JVM 9+).
fun labelTemplate(id: Int, name: String): String = "user-$id:$name"

// Card: groupingBy { }.eachCount() instead of groupBy { }.mapValues.
fun countsBaseline(words: List<String>): Map<String, Int> =
    words.groupBy { it }.mapValues { it.value.size }

fun countsCandidate(words: List<String>): Map<String, Int> =
    words.groupingBy { it }.eachCount()

// Card: associateWith instead of associate { it to f(it) }.
fun lengthsBaseline(words: List<String>): Map<String, Int> =
    words.associate { it to it.length }

fun lengthsCandidate(words: List<String>): Map<String, Int> =
    words.associateWith { it.length }

object CollectionChecks {
    fun run() {
        val values = List(10_000) { it - 5_000 }
        for (limit in listOf(0, 1, 10, 20_000)) {
            Harness.equal(
                "sequence take $limit",
                firstSquaresBaseline(values, limit),
                firstSquaresCandidate(values, limit),
            )
        }
        // Salvaged trap: lazy chains skip side effects the eager chain ran.
        var eagerCalls = 0
        listOf(1, 2, 3).map { eagerCalls++; it }.take(1)
        var lazyCalls = 0
        listOf(1, 2, 3).asSequence().map { lazyCalls++; it }.take(1).toList()
        Harness.equal("sequence side effects eager", 3, eagerCalls)
        Harness.equal("sequence side effects lazy", 1, lazyCalls)
        Harness.alloc(
            "sequence take 10",
            Expect.LESS,
            { firstSquaresBaseline(values, 10) },
            { firstSquaresCandidate(values, 10) },
        )

        val small = List(16) { it - 8 }
        Harness.equal(
            "small chain",
            smallChainIterable(small),
            smallChainSequence(small),
        )
        Harness.alloc(
            "small chain (sequence vs iterable)",
            Expect.REPORT,
            { smallChainIterable(small) },
            { smallChainSequence(small) },
        )

        val words = List(1_000) { "w" + (it % 37) }
        Harness.equal(
            "sumOf",
            totalLengthBaseline(words),
            totalLengthCandidate(words),
        )
        Harness.alloc(
            "sumOf",
            Expect.ZERO,
            { totalLengthBaseline(words) },
            { totalLengthCandidate(words) },
        )

        var calls = 0
        val twiceBaseline = sequenceTwiceBaseline { calls++; 10 }
        val baselineCalls = calls
        calls = 0
        val twiceCandidate = sequenceTwiceCandidate { calls++; 10 }
        Harness.equal("sequence reuse result", twiceBaseline, twiceCandidate)
        Harness.equal("sequence reuse baseline calls", 8, baselineCalls)
        Harness.equal("sequence reuse candidate calls", 4, calls)

        val ints = IntArray(1_000) { it * 5 }
        Harness.equal("buildList", appendBaseline(ints), appendCandidate(ints))
        Harness.equal("buildList empty", emptyList<Int>(), appendCandidate(IntArray(0)))
        Harness.alloc(
            "buildList",
            Expect.LESS,
            { appendBaseline(ints) },
            { appendCandidate(ints) },
        )

        val parts = List(500) { "p$it" } + listOf("", "é", "🙂")
        Harness.equal("buildString", joinBaseline(parts), joinCandidate(parts))
        Harness.equal("buildString empty", "", joinCandidate(emptyList()))
        Harness.alloc(
            "buildString",
            Expect.LESS,
            { joinBaseline(parts) },
            { joinCandidate(parts) },
        )

        Harness.equal("template", "user-7:ann", labelTemplate(7, "ann"))

        val unicode = words + listOf("é", "é", "é", "🙂")
        Harness.equal("groupingBy", countsBaseline(unicode), countsCandidate(unicode))
        Harness.equal(
            "groupingBy order",
            countsBaseline(unicode).keys.toList(),
            countsCandidate(unicode).keys.toList(),
        )
        Harness.alloc(
            "groupingBy",
            Expect.LESS,
            { countsBaseline(words) },
            { countsCandidate(words) },
        )

        val distinct = List(1_000) { "key$it" }
        Harness.equal(
            "associateWith",
            lengthsBaseline(distinct + "key1"),
            lengthsCandidate(distinct + "key1"),
        )
        Harness.alloc(
            "associateWith",
            Expect.REPORT,
            { lengthsBaseline(distinct) },
            { lengthsCandidate(distinct) },
        )
    }
}
