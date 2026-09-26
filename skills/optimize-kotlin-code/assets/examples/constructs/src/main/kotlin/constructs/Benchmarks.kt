package constructs

import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.openjdk.jmh.annotations.Benchmark
import org.openjdk.jmh.annotations.BenchmarkMode
import org.openjdk.jmh.annotations.Fork
import org.openjdk.jmh.annotations.Measurement
import org.openjdk.jmh.annotations.Mode
import org.openjdk.jmh.annotations.OutputTimeUnit
import org.openjdk.jmh.annotations.Scope
import org.openjdk.jmh.annotations.State
import org.openjdk.jmh.annotations.Warmup

// JMH needs open classes; Kotlin classes are final by default.
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(1)
open class Pairs {
    private val ints = IntArray(1_000) { it * 7 % 1_000 }
    private val list = List(10_000) { it - 5_000 }
    private val small = List(16) { it - 8 }
    private val words = List(1_000) { "w" + (it % 37) }
    private val parts = List(500) { "p$it" }
    private val mixed: List<Any> = List(1_000) { if (it % 3 == 0) "s$it" else it }
    private val stats = IntArray(1_000) { (it * 37) % 501 - 250 }
    private val keyA = RouteKey("/api/" + "segment/".repeat(128), 1)
    private val keyB = RouteKey(String(keyA.path.toCharArray()), 2)
    private val fastA = RouteKeyFast(keyA.path, 1)
    private val fastB = RouteKeyFast(keyB.path, 2)
    private val shapes: List<Shape> = List(1_000) {
        when (it % 3) {
            0 -> Square(it.toDouble())
            1 -> Circle(it.toDouble())
            else -> Rect(it.toDouble(), 2.0)
        }
    }
    private val report = ReportSync(small)
    private val reportNone = ReportNone(small)
    private val reportEager = ReportEager(small)
    private val mutex = Mutex()
    private val lock = Any()
    private val atomic = AtomicInteger()
    private var plain = 0

    @Benchmark
    fun inlineBaseline() = countAboveBaseline(ints, 500)
    @Benchmark
    fun inlineCandidate() = countAboveCandidate(ints, 500)
    @Benchmark
    fun capturedBaseline() = sumCapturedBaseline(ints)
    @Benchmark
    fun capturedCandidate() = sumCapturedCandidate(ints)
    @Benchmark
    fun reifiedBaseline() = stringsBaseline(mixed)
    @Benchmark
    fun reifiedCandidate() = stringsCandidate(mixed)

    @Benchmark
    fun boxedListBaseline() = squaresBaseline(1_000)
    @Benchmark
    fun boxedListCandidate() = squaresCandidate(1_000)
    @Benchmark
    fun nullableBaseline() = maxOrNullBaseline(ints)
    @Benchmark
    fun nullableCandidate() = maxOrNullCandidate(ints)
    @Benchmark
    fun copyBaseline() = statsBaseline(stats)
    @Benchmark
    fun copyCandidate() = statsCandidate(stats)
    @Benchmark
    fun equalsBaseline() = keyA == keyB
    @Benchmark
    fun equalsCandidate() = fastA == fastB

    @Benchmark
    fun takeBaseline() = firstSquaresBaseline(list, 10)
    @Benchmark
    fun takeCandidate() = firstSquaresCandidate(list, 10)
    @Benchmark
    fun smallIterable() = smallChainIterable(small)
    @Benchmark
    fun smallSequence() = smallChainSequence(small)
    @Benchmark
    fun sumOfBaseline() = totalLengthBaseline(words)
    @Benchmark
    fun sumOfCandidate() = totalLengthCandidate(words)
    @Benchmark
    fun joinBaselineBench() = joinBaseline(parts)
    @Benchmark
    fun joinCandidateBench() = joinCandidate(parts)
    @Benchmark
    fun countsBaselineBench() = countsBaseline(words)
    @Benchmark
    fun countsCandidateBench() = countsCandidate(words)

    @Benchmark
    fun stepBaseline() = sumEvenStepBaseline(ints)
    @Benchmark
    fun stepCandidate() = sumEvenStepCandidate(ints)
    @Benchmark
    fun forEachRange() = sumForEachBaseline(ints)
    @Benchmark
    fun untilRange() = sumUntil(ints)
    @Benchmark
    fun sealedWhen() = shapes.sumOf { areaWhen(it) }

    @Benchmark
    fun lazySyncRead() = report.total
    @Benchmark
    fun lazyNoneRead() = reportNone.total
    @Benchmark
    fun eagerRead() = reportEager.total

    @Benchmark
    fun mutexIncrement() = runBlocking {
        repeat(100) { mutex.withLock { plain++ } }
        plain
    }

    @Benchmark
    fun synchronizedIncrement() = runBlocking {
        repeat(100) { synchronized(lock) { plain++ } }
        plain
    }

    @Benchmark
    fun atomicIncrement() = runBlocking {
        repeat(100) { atomic.incrementAndGet() }
        atomic.get()
    }

    @Benchmark
    fun runBlockingBaseline() = squaresRunBlockingBaseline(100)
    @Benchmark
    fun runBlockingCandidate() = squaresSuspendCandidate(100)
}
