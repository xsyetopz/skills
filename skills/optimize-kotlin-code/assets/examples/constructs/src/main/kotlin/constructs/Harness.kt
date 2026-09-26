package constructs

import java.lang.management.ManagementFactory

/** Minimal oracle and allocation counter shared by every construct pair. */
object Harness {
    private val threads =
        ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean

    @Volatile
    var sink: Any? = null
    var failures = 0
        private set

    fun equal(name: String, expected: Any?, actual: Any?) {
        if (expected == actual) {
            println("PASS $name")
        } else {
            println("FAIL $name: expected <$expected>, got <$actual>")
            failures++
        }
    }

    fun that(name: String, ok: Boolean, detail: String) {
        println((if (ok) "PASS " else "FAIL ") + "$name: $detail")
        if (!ok) failures++
    }

    /**
     * Bytes allocated on this thread per call of [body], measured after
     * [warm] calls so the JIT has compiled the path (run with -Xbatch).
     */
    fun bytesPerCall(
        warm: Int = 30_000,
        runs: Int = 2_000,
        body: () -> Any?,
    ): Long {
        repeat(warm) { sink = body() }
        val before = threads.currentThreadAllocatedBytes
        repeat(runs) { sink = body() }
        return (threads.currentThreadAllocatedBytes - before) / runs
    }

    /**
     * The lambda returns Any?, so a primitive result is boxed on every
     * call. Measure that boxing alone for a sample result and subtract it.
     */
    private fun boxOverhead(sample: Any?): Long = when (sample) {
        is Int -> sample.let { v: Int -> bytesPerCall { v } }
        is Long -> sample.let { v: Long -> bytesPerCall { v } }
        is Double -> sample.let { v: Double -> bytesPerCall { v } }
        else -> 0
    }

    enum class Expect { LESS, ZERO, REPORT }

    /** verify.sh noea sets this: without escape analysis only report. */
    private val reportOnly = System.getProperty("constructs.reportOnly") != null

    /**
     * Prints baseline and candidate bytes per call, net of result boxing.
     * LESS asserts the candidate allocates less; ZERO asserts it allocates
     * nothing; REPORT only records the numbers (escape analysis may have
     * erased the baseline allocation).
     */
    fun alloc(
        name: String,
        expect: Expect,
        baseline: () -> Any?,
        candidate: () -> Any?,
    ) {
        val b = bytesPerCall(body = baseline) - boxOverhead(baseline())
        val c = bytesPerCall(body = candidate) - boxOverhead(candidate())
        val detail = "baseline $b B/call, candidate $c B/call"
        when (if (reportOnly) Expect.REPORT else expect) {
            Expect.LESS -> that("alloc $name", c < b, detail)
            Expect.ZERO -> that("alloc $name", c == 0L, detail)
            Expect.REPORT -> println("INFO alloc $name: $detail")
        }
    }
}
