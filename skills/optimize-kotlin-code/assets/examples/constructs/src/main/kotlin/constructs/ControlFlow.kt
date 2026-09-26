package constructs

import constructs.Harness.Expect
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Card: range loops the compiler lowers to counted int loops.
fun sumUntil(xs: IntArray): Long {
    var s = 0L
    for (i in 0 until xs.size) s += xs[i]
    return s
}

fun sumRangeUntil(xs: IntArray): Long {
    var s = 0L
    for (i in 0..<xs.size) s += xs[i]
    return s
}

fun sumIndices(xs: IntArray): Long {
    var s = 0L
    for (i in xs.indices) s += xs[i]
    return s
}

fun sumDownTo(xs: IntArray): Long {
    var s = 0L
    for (i in xs.size - 1 downTo 0) s += xs[i]
    return s
}

fun sumListIndices(xs: List<Int>): Long {
    var s = 0L
    for (i in xs.indices) s += xs[i]
    return s
}

// Card: range objects (step, reversed, forEach, stored ranges).
fun sumEvenStepBaseline(xs: IntArray): Long {
    var s = 0L
    for (i in 0 until xs.size step 2) s += xs[i]
    return s
}

fun sumEvenStepCandidate(xs: IntArray): Long {
    var s = 0L
    var i = 0
    while (i < xs.size) {
        s += xs[i]
        i += 2
    }
    return s
}

fun sumForEachBaseline(xs: IntArray): Long {
    var s = 0L
    (0 until xs.size).forEach { s += xs[it] }
    return s
}

fun sumReversedBaseline(xs: IntArray): Long {
    var s = 0L
    for (i in (0 until xs.size).reversed()) s += xs[i]
    return s
}

// Cards: when over sealed types, enums, and strings.
sealed interface Shape

class Square(val side: Double) : Shape

class Circle(val radius: Double) : Shape

class Rect(val w: Double, val h: Double) : Shape

fun areaWhen(shape: Shape): Double = when (shape) {
    is Square -> shape.side * shape.side
    is Circle -> 3.0 * shape.radius * shape.radius
    is Rect -> shape.w * shape.h
}

enum class Level { DEBUG, INFO, WARN, ERROR }

fun weightWhen(level: Level): Int = when (level) {
    Level.DEBUG -> 1
    Level.INFO -> 2
    Level.WARN -> 4
    Level.ERROR -> 8
}

fun methodWhen(method: String): Int = when (method) {
    "GET" -> 1
    "PUT" -> 2
    "POST" -> 3
    "DELETE" -> 4
    else -> 0
}

// Cards: lazy modes.
class ReportSync(private val rows: List<Int>) {
    val total: Int by lazy { rows.sum() }
}

class ReportPublication(private val rows: List<Int>) {
    val total: Int by lazy(LazyThreadSafetyMode.PUBLICATION) { rows.sum() }
}

class ReportNone(private val rows: List<Int>) {
    val total: Int by lazy(LazyThreadSafetyMode.NONE) { rows.sum() }
}

class ReportEager(rows: List<Int>) {
    val total: Int = rows.sum()
}

/**
 * Runs two threads against one Lazy whose initializer waits up to 1 s
 * for a second initializer to start. Returns how many initializers ran.
 */
fun initializerRuns(mode: LazyThreadSafetyMode): Int {
    val runs = AtomicInteger()
    val both = CountDownLatch(2)
    val value = lazy(mode) {
        runs.incrementAndGet()
        both.countDown()
        both.await(1_000, TimeUnit.MILLISECONDS)
        42
    }
    val results = IntArray(2)
    val workers = List(2) { i -> thread { results[i] = value.value } }
    workers.forEach { it.join() }
    check(results[0] == 42 && results[1] == 42)
    return runs.get()
}

object ControlFlowChecks {
    fun run() {
        val xs = IntArray(1_000) { it * 3 - 700 }
        val expected = xs.fold(0L) { acc, v -> acc + v }
        for ((name, got) in listOf(
            "until" to sumUntil(xs),
            "..<" to sumRangeUntil(xs),
            "indices" to sumIndices(xs),
            "downTo" to sumDownTo(xs),
            "list indices" to sumListIndices(xs.toList()),
            "forEach" to sumForEachBaseline(xs),
            "reversed" to sumReversedBaseline(xs),
        )) {
            Harness.equal("range $name", expected, got)
        }
        for (input in listOf(IntArray(0), intArrayOf(5), IntArray(7) { it })) {
            Harness.equal(
                "range step ${input.size}",
                sumEvenStepBaseline(input),
                sumEvenStepCandidate(input),
            )
        }
        Harness.alloc(
            "range step",
            Expect.LESS,
            { sumEvenStepBaseline(xs) },
            { sumEvenStepCandidate(xs) },
        )
        Harness.alloc(
            "range forEach/reversed",
            Expect.LESS,
            { sumForEachBaseline(xs) + sumReversedBaseline(xs) },
            { sumUntil(xs) + sumDownTo(xs) },
        )

        Harness.equal("when sealed", 12.0, areaWhen(Rect(3.0, 4.0)))
        Harness.equal("when enum", 15, Level.entries.sumOf { weightWhen(it) })
        Harness.equal("when string", listOf(3, 0), listOf("POST", "post").map(::methodWhen))

        val rows = List(100) { it }
        Harness.equal("lazy sync", 4_950, ReportSync(rows).total)
        Harness.equal("lazy publication", 4_950, ReportPublication(rows).total)
        Harness.equal("lazy none", 4_950, ReportNone(rows).total)
        Harness.equal(
            "lazy synchronized initializer runs",
            1,
            initializerRuns(LazyThreadSafetyMode.SYNCHRONIZED),
        )
        Harness.equal(
            "lazy publication initializer runs",
            2,
            initializerRuns(LazyThreadSafetyMode.PUBLICATION),
        )
        Harness.alloc(
            "lazy per instance (sync vs eager)",
            Expect.LESS,
            { ReportSync(rows) },
            { ReportEager(rows) },
        )
        Harness.alloc(
            "lazy per instance (none vs sync)",
            Expect.REPORT,
            { ReportSync(rows) },
            { ReportNone(rows) },
        )
    }
}
