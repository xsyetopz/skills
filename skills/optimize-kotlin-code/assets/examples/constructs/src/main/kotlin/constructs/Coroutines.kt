@file:OptIn(ExperimentalCoroutinesApi::class, DelicateCoroutinesApi::class)

package constructs

import constructs.Harness.Expect
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext

// Cards: Dispatchers.IO for blocking calls; limitedParallelism.
/**
 * Launches [tasks] coroutines that each block their thread (a latch wait
 * standing in for JDBC or file I/O) and returns the peak number that
 * were blocked at the same time.
 */
fun peakBlocking(
    dispatcher: CoroutineDispatcher,
    tasks: Int,
    waitMillis: Long = 100,
): Int =
    runBlocking {
        val active = AtomicInteger()
        val peak = AtomicInteger()
        val arrived = CountDownLatch(tasks)
        List(tasks) {
            launch(dispatcher) {
                peak.accumulateAndGet(active.incrementAndGet(), ::maxOf)
                arrived.countDown()
                arrived.await(waitMillis, TimeUnit.MILLISECONDS) // blocking
                active.decrementAndGet()
            }
        }.joinAll()
        peak.get()
    }

// Card: structured concurrency instead of GlobalScope.
fun childOutlivesCancelledParent(structured: Boolean): Boolean {
    val finished = AtomicBoolean(false)
    runBlocking {
        val parent = launch(Dispatchers.Default) {
            val work: suspend () -> Unit = {
                delay(100)
                finished.set(true)
            }
            if (structured) launch { work() } else GlobalScope.launch { work() }
            awaitCancellation()
        }
        delay(20)
        parent.cancelAndJoin()
        delay(1_000)
    }
    return finished.get()
}

// Card: async/awaitAll for independent suspending calls.
suspend fun fetchPrice(id: Int): Int {
    delay(100)
    return id * 10
}

suspend fun pricesSequential(ids: List<Int>): List<Int> =
    ids.map { fetchPrice(it) }

suspend fun pricesConcurrent(ids: List<Int>): List<Int> = coroutineScope {
    ids.map { async { fetchPrice(it) } }.awaitAll()
}

// Card: no runBlocking in hot paths.
suspend fun square(x: Int): Int = x * x

fun squaresRunBlockingBaseline(n: Int): Int {
    var sum = 0
    repeat(n) { sum += runBlocking { square(it) } }
    return sum
}

fun squaresSuspendCandidate(n: Int): Int = runBlocking {
    var sum = 0
    repeat(n) { sum += square(it) }
    sum
}

// Cards: Flow buffer, conflate, flowOn.
fun ticks(): Flow<Int> = flow {
    for (i in 1..3) {
        delay(100) // producer cost
        emit(i)
    }
}

fun virtualCollect(transform: (Flow<Int>) -> Flow<Int>): Pair<List<Int>, Long> {
    val seen = ArrayList<Int>()
    var elapsed = 0L
    runTest {
        transform(ticks()).collect {
            delay(300) // consumer cost
            seen += it
        }
        elapsed = testScheduler.currentTime
    }
    return seen to elapsed
}

fun upstreamThreadBaseline(): String = runBlocking {
    var name = ""
    flow {
        withContext(Dispatchers.Default) { emit(Thread.currentThread().name) }
    }.collect { name = it }
    name
}

fun upstreamThreadCandidate(): Pair<String, String> = runBlocking {
    var upstream = ""
    var downstream = ""
    flow { emit(Thread.currentThread().name) }
        .flowOn(Dispatchers.Default)
        .collect {
            upstream = it
            downstream = Thread.currentThread().name
        }
    upstream to downstream
}

// Cards: Mutex for suspending critical sections; atomics or synchronized
// for non-suspending ones.
fun lostUpdatesBaseline(workers: Int): Int {
    var counter = 0
    runTest {
        List(workers) {
            launch {
                val read = counter
                delay(1) // suspension inside the read-modify-write
                counter = read + 1
            }
        }.joinAll()
    }
    return counter
}

fun lostUpdatesCandidate(workers: Int): Int {
    var counter = 0
    val mutex = Mutex()
    runTest {
        List(workers) {
            launch {
                mutex.withLock {
                    val read = counter
                    delay(1)
                    counter = read + 1
                }
            }
        }.joinAll()
    }
    return counter
}

fun incrementWithMutex(coroutines: Int, each: Int): Int = runBlocking {
    val mutex = Mutex()
    var counter = 0
    List(coroutines) {
        launch(Dispatchers.Default) {
            repeat(each) { mutex.withLock { counter++ } }
        }
    }.joinAll()
    counter
}

fun incrementWithAtomic(coroutines: Int, each: Int): Int = runBlocking {
    val counter = AtomicInteger()
    List(coroutines) {
        launch(Dispatchers.Default) {
            repeat(each) { counter.incrementAndGet() }
        }
    }.joinAll()
    counter.get()
}

// Card: Channel capacity.
/** Virtual time at which the producer finished sending 5 items. */
fun producerDoneAt(capacity: Int): Long {
    var doneAt = -1L
    runTest {
        val channel = Channel<Int>(capacity)
        launch {
            repeat(5) { channel.send(it) }
            doneAt = testScheduler.currentTime
            channel.close()
        }
        for (item in channel) delay(100)
    }
    return doneAt
}

// Card: rethrow CancellationException.
fun iterationsAfterCancel(rethrow: Boolean): Int {
    var iterations = 0
    runTest {
        val job = launch {
            repeat(50) {
                try {
                    delay(10)
                } catch (e: Exception) {
                    if (rethrow && e is CancellationException) throw e
                }
                iterations++
            }
        }
        delay(25)
        job.cancelAndJoin()
    }
    return iterations
}

// Card: ensureActive in CPU-bound loops.
fun chunksAfterCancel(checkActive: Boolean): Int = runBlocking {
    val done = AtomicInteger()
    val started = CountDownLatch(1)
    val cancelled = CountDownLatch(1)
    val job = launch(Dispatchers.Default) {
        for (chunk in 0 until 20) {
            if (checkActive) ensureActive()
            if (chunk == 1) {
                started.countDown()
                cancelled.await()
            }
            done.incrementAndGet()
        }
    }
    started.await()
    job.cancel()
    cancelled.countDown()
    job.join()
    done.get()
}

object CoroutineChecks {
    fun run() {
        val cores = Runtime.getRuntime().availableProcessors()
        val onDefault = peakBlocking(Dispatchers.Default, 32)
        // Returns as soon as all 32 arrive; the long wait only matters on
        // a loaded machine.
        val onIo = peakBlocking(Dispatchers.IO, 32, waitMillis = 5_000)
        Harness.that(
            "dispatcher default blocks",
            onDefault <= cores,
            "peak $onDefault blocked on Default (cores $cores)",
        )
        Harness.equal("dispatcher io peak", 32, onIo)
        val limited = peakBlocking(Dispatchers.IO.limitedParallelism(4), 16)
        Harness.equal("limitedParallelism peak", 4, limited)

        Harness.equal("globalscope leak", true, childOutlivesCancelledParent(false))
        Harness.equal("structured cancel", false, childOutlivesCancelledParent(true))

        val ids = listOf(1, 2, 3)
        var seqTime = 0L
        var seq = emptyList<Int>()
        runTest {
            seq = pricesSequential(ids)
            seqTime = testScheduler.currentTime
        }
        var conTime = 0L
        var con = emptyList<Int>()
        runTest {
            con = pricesConcurrent(ids)
            conTime = testScheduler.currentTime
        }
        Harness.equal("async awaitAll result", seq, con)
        Harness.equal("async virtual time sequential", 300L, seqTime)
        Harness.equal("async virtual time concurrent", 100L, conTime)

        Harness.equal(
            "runBlocking result",
            squaresRunBlockingBaseline(100),
            squaresSuspendCandidate(100),
        )
        Harness.alloc(
            "runBlocking per call",
            Expect.LESS,
            { squaresRunBlockingBaseline(100) },
            { squaresSuspendCandidate(100) },
        )

        Harness.equal("flow plain", listOf(1, 2, 3) to 1_200L, virtualCollect { it })
        Harness.equal(
            "flow buffer",
            listOf(1, 2, 3) to 1_000L,
            virtualCollect { it.buffer() },
        )
        Harness.equal(
            "flow conflate",
            listOf(1, 3) to 700L,
            virtualCollect { it.conflate() },
        )
        val invariant = runCatching { upstreamThreadBaseline() }.exceptionOrNull()
        Harness.that(
            "flow withContext rejected",
            invariant is IllegalStateException &&
                    "Flow invariant is violated" in invariant.message.orEmpty(),
            "${invariant?.javaClass?.simpleName}",
        )
        val (up, down) = upstreamThreadCandidate()
        Harness.that(
            "flowOn threads",
            "DefaultDispatcher-worker" in up && "DefaultDispatcher" !in down,
            "upstream=$up downstream=$down",
        )

        Harness.equal("mutex lost updates baseline", 1, lostUpdatesBaseline(100))
        Harness.equal("mutex serialized", 100, lostUpdatesCandidate(100))
        Harness.equal("mutex counter", 80_000, incrementWithMutex(8, 10_000))
        Harness.equal("atomic counter", 80_000, incrementWithAtomic(8, 10_000))

        Harness.equal("channel rendezvous", 400L, producerDoneAt(Channel.RENDEZVOUS))
        Harness.equal("channel buffered", 0L, producerDoneAt(Channel.BUFFERED))

        Harness.equal("cancellation swallowed", 50, iterationsAfterCancel(false))
        Harness.equal("cancellation rethrown", 2, iterationsAfterCancel(true))

        Harness.equal("ensureActive absent", 20, chunksAfterCancel(false))
        Harness.equal("ensureActive present", 2, chunksAfterCancel(true))
    }
}
