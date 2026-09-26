package constructs

import constructs.Harness.Expect

// Card: value class used as its own type.
class CentsBox(val value: Long) {
    operator fun plus(other: CentsBox) = CentsBox(value + other.value)
}

@JvmInline
value class Cents(val value: Long) {
    operator fun plus(other: Cents) = Cents(value + other.value)
}

fun totalBaseline(prices: LongArray): CentsBox {
    var total = CentsBox(0)
    for (price in prices) total += CentsBox(price)
    return total
}

fun totalCandidate(prices: LongArray): Cents {
    var total = Cents(0)
    for (price in prices) total += Cents(price)
    return total
}

// Card: value class boxing at generic, nullable, and interface boundaries.
fun pricesBaseline(raw: LongArray): List<Cents> = raw.map { Cents(it) }

/** Stores the underlying longs; like kotlin.ULongArray over LongArray. */
@JvmInline
value class CentsArray(val raw: LongArray) {
    val size: Int get() = raw.size

    operator fun get(index: Int): Cents = Cents(raw[index])
}

fun pricesCandidate(raw: LongArray): CentsArray = CentsArray(raw.copyOf())

fun firstOrNullBaseline(prices: List<Cents>): Cents? = prices.firstOrNull()

// Card: primitive arrays instead of List<Int> and Array<Int>.
fun squaresBaseline(n: Int): List<Int> = List(n) { (it + 200) * 3 }

fun squaresArrayBaseline(n: Int): Array<Int> = Array(n) { (it + 200) * 3 }

fun squaresCandidate(n: Int): IntArray = IntArray(n) { (it + 200) * 3 }

// Card: non-null primitive locals instead of Int?.
fun maxOrNullBaseline(values: IntArray): Int? {
    var best: Int? = null
    for (value in values) if (best == null || value > best) best = value
    return best
}

fun maxOrNullCandidate(values: IntArray): Int? {
    if (values.isEmpty()) return null
    var best = values[0]
    for (i in 1 until values.size) if (values[i] > best) best = values[i]
    return best
}

// Card: const val versus val (read from another file: Consts.kt).
fun bufferSizeBaseline(): Int = PLAIN_BUFFER_SIZE * 2

fun bufferSizeCandidate(): Int = CONST_BUFFER_SIZE * 2

// Cards: @JvmField and @JvmStatic. Kotlin call sites.
fun readPropertyBaseline(p: Point): Int = p.x + Point.origin()

fun readPropertyCandidate(p: Point): Int = p.y + Point.originStatic()

// Card: data class copy in a hot loop.
data class Stats(val count: Int, val sum: Long, val max: Int)

fun statsBaseline(values: IntArray): Stats {
    var stats = Stats(0, 0, Int.MIN_VALUE)
    for (v in values) {
        stats = stats.copy(
            count = stats.count + 1,
            sum = stats.sum + v,
            max = maxOf(stats.max, v),
        )
    }
    return stats
}

fun statsCandidate(values: IntArray): Stats {
    var count = 0
    var sum = 0L
    var max = Int.MIN_VALUE
    for (v in values) {
        count++
        sum += v
        max = maxOf(max, v)
    }
    return Stats(count, sum, max)
}

// Card: data class equals property order.
data class RouteKey(val path: String, val version: Int)

/** Same fields; equals compares the cheap discriminating Int first. */
class RouteKeyFast(val path: String, val version: Int) {
    override fun equals(other: Any?): Boolean =
        other is RouteKeyFast && version == other.version &&
                path == other.path

    override fun hashCode(): Int = 31 * path.hashCode() + version
}

object RepresentationChecks {
    fun run() {
        val prices = LongArray(1_000) { it * 3L + 1 }
        Harness.equal(
            "value class total",
            totalBaseline(prices).value,
            totalCandidate(prices).value,
        )
        Harness.alloc(
            "value class total",
            Expect.ZERO,
            { totalBaseline(prices) },
            { totalCandidate(prices).value },
        )

        val boxed = pricesBaseline(prices)
        val packed = pricesCandidate(prices)
        Harness.equal("value class storage size", boxed.size, packed.size)
        Harness.that(
            "value class storage elements",
            boxed.indices.all { boxed[it] == packed[it] },
            "every element equal",
        )
        Harness.equal("value class nullable", Cents(1), firstOrNullBaseline(boxed))
        Harness.equal("value class nullable empty", null, firstOrNullBaseline(emptyList()))
        Harness.alloc(
            "value class storage",
            Expect.LESS,
            { pricesBaseline(prices) },
            { pricesCandidate(prices).raw },
        )

        Harness.equal(
            "primitive array",
            squaresBaseline(1_000),
            squaresCandidate(1_000).toList(),
        )
        Harness.equal(
            "boxed array",
            squaresArrayBaseline(1_000).toList(),
            squaresCandidate(1_000).toList(),
        )
        Harness.alloc(
            "primitive array vs List<Int>",
            Expect.LESS,
            { squaresBaseline(1_000) },
            { squaresCandidate(1_000) },
        )
        Harness.alloc(
            "primitive array vs Array<Int>",
            Expect.LESS,
            { squaresArrayBaseline(1_000) },
            { squaresCandidate(1_000) },
        )

        for (input in listOf(intArrayOf(), intArrayOf(-5), intArrayOf(3, 900, 7))) {
            Harness.equal(
                "nullable local ${input.toList()}",
                maxOrNullBaseline(input),
                maxOrNullCandidate(input),
            )
        }
        val ramp = IntArray(1_000) { it + 1_000 }
        Harness.alloc(
            "nullable local",
            Expect.LESS,
            { maxOrNullBaseline(ramp) },
            { maxOrNullCandidate(ramp) },
        )

        Harness.equal("const val", bufferSizeBaseline(), bufferSizeCandidate())
        val point = Point(4, 4)
        Harness.equal(
            "jvmfield/jvmstatic",
            readPropertyBaseline(point),
            readPropertyCandidate(point),
        )

        val stats = IntArray(1_000) { (it * 37) % 501 - 250 }
        Harness.equal("data copy", statsBaseline(stats), statsCandidate(stats))
        Harness.equal(
            "data copy empty",
            statsBaseline(IntArray(0)),
            statsCandidate(IntArray(0)),
        )
        Harness.alloc(
            "data copy",
            Expect.LESS,
            { statsBaseline(stats) },
            { statsCandidate(stats) },
        )

        val longPath = "/api/" + "segment/".repeat(128)
        val a = RouteKey(String(longPath.toCharArray()), 1)
        val b = RouteKey(String(longPath.toCharArray()), 2)
        val fa = RouteKeyFast(a.path, 1)
        val fb = RouteKeyFast(b.path, 2)
        Harness.equal("data equals differs", a == b, fa == fb)
        Harness.equal(
            "data equals same",
            a == a.copy(),
            fa == RouteKeyFast(String(fa.path.toCharArray()), 1),
        )
    }
}
