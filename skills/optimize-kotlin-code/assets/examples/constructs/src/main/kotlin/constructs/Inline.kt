package constructs

import constructs.Harness.Expect

// Card: inline higher-order function.
// Baseline: a regular higher-order function. The lambda is a Function1
// object; each call boxes the Int argument and the Boolean result.
fun countIfBaseline(values: IntArray, predicate: (Int) -> Boolean): Int {
    var count = 0
    for (value in values) if (predicate(value)) count++
    return count
}

inline fun countIfCandidate(
    values: IntArray,
    predicate: (Int) -> Boolean,
): Int {
    var count = 0
    for (value in values) if (predicate(value)) count++
    return count
}

fun countAboveBaseline(values: IntArray, limit: Int): Int =
    countIfBaseline(values) { it > limit }

fun countAboveCandidate(values: IntArray, limit: Int): Int =
    countIfCandidate(values) { it > limit }

// Card: captured var in a non-inline lambda (Ref.IntRef).
fun eachBaseline(values: IntArray, action: (Int) -> Unit) {
    for (value in values) action(value)
}

fun sumCapturedBaseline(values: IntArray): Int {
    var sum = 0
    eachBaseline(values) { sum += it }
    return sum
}

fun sumCapturedCandidate(values: IntArray): Int {
    var sum = 0
    values.forEach { sum += it } // stdlib forEach is inline
    return sum
}

// Card: reified type parameter.
fun <T> countInstancesBaseline(items: List<Any>, type: Class<T>): Int =
    items.count { type.isInstance(it) }

inline fun <reified T> countInstancesCandidate(items: List<Any>): Int =
    items.count { it is T }

fun stringsBaseline(items: List<Any>): Int =
    countInstancesBaseline(items, String::class.java)

fun stringsCandidate(items: List<Any>): Int =
    countInstancesCandidate<String>(items)

// Card: noinline parameter.
val listeners = ArrayList<() -> Unit>()

// Baseline: the whole function is non-inline because one lambda is stored.
fun registerBaseline(now: () -> Unit, later: () -> Unit) {
    now()
    listeners.add(later)
}

// Candidate: only the stored lambda becomes an object.
inline fun registerCandidate(now: () -> Unit, noinline later: () -> Unit) {
    now()
    listeners.add(later)
}

fun useRegisterBaseline(log: StringBuilder, id: Int) =
    registerBaseline({ log.append(id) }, { log.append(-id) })

fun useRegisterCandidate(log: StringBuilder, id: Int) =
    registerCandidate({ log.append(id) }, { log.append(-id) })

// Card: crossinline parameter.
// Baseline: body is a Function0 object wrapped by a Runnable object.
fun deferBaseline(body: () -> Unit): Runnable = Runnable { body() }

// Candidate: one generated Runnable class per call site, body inlined.
inline fun deferCandidate(crossinline body: () -> Unit): Runnable =
    Runnable { body() }

fun useDeferBaseline(log: StringBuilder, id: Int): Runnable =
    deferBaseline { log.append(id) }

fun useDeferCandidate(log: StringBuilder, id: Int): Runnable =
    deferCandidate { log.append(id) }

object InlineChecks {
    fun run() {
        val values = IntArray(1_000) { it * 7 % 1_000 }
        Harness.equal(
            "inline countIf",
            countAboveBaseline(values, 500),
            countAboveCandidate(values, 500),
        )
        Harness.equal("inline countIf empty", 0, countAboveCandidate(IntArray(0), 0))
        Harness.alloc(
            "inline countIf",
            Expect.REPORT,
            { countAboveBaseline(values, 500) },
            { countAboveCandidate(values, 500) },
        )

        Harness.equal(
            "captured var",
            sumCapturedBaseline(values),
            sumCapturedCandidate(values),
        )
        Harness.alloc(
            "captured var",
            Expect.REPORT,
            { sumCapturedBaseline(values) },
            { sumCapturedCandidate(values) },
        )

        val mixed: List<Any> = listOf("a", 1, "b", 2.0, 'c', "d", listOf("e"))
        Harness.equal("reified", stringsBaseline(mixed), stringsCandidate(mixed))
        Harness.equal("reified count", 3, stringsCandidate(mixed))

        val log = StringBuilder()
        listeners.clear()
        useRegisterBaseline(log, 1)
        useRegisterCandidate(log, 2)
        listeners.forEach { it() }
        Harness.equal("noinline order", "12-1-2", log.toString())
        listeners.clear()

        val deferred = StringBuilder()
        val tasks = listOf(
            useDeferBaseline(deferred, 1),
            useDeferCandidate(deferred, 2),
        )
        Harness.equal("crossinline deferred", "", deferred.toString())
        tasks.forEach { it.run() }
        Harness.equal("crossinline ran", "12", deferred.toString())
        Harness.alloc(
            "crossinline",
            Expect.LESS,
            { useDeferBaseline(deferred, 1) },
            { useDeferCandidate(deferred, 1) },
        )
    }
}
