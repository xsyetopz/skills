import java.util.Locale
import java.util.concurrent.atomic.AtomicInteger
import kotlin.system.exitProcess

private fun contract(bad: Boolean, topic: Int): Boolean = when (topic) {
    1 -> { // All side effects are required, even when only the first value is returned.
        var calls = 0
        if (bad) sequenceOf(1,2,3).map { calls++; it }.take(1).toList()
        else listOf(1,2,3).map { calls++; it }.take(1)
        calls == 3
    }
    2 -> { // Repeat reads must not rerun a side-effecting source.
        var calls = 0
        val sequence = sequenceOf(1,2).onEach { calls++ }
        if (bad) { sequence.toList(); sequence.toList() }
        else { val cached = sequence.toList(); cached.toList(); cached.toList() }
        calls == 2
    }
    3 -> { // Preserve duplicate values and their order.
        val values = listOf(2,1,2)
        val result = if (bad) values.toSet().toList() else values.toList()
        result == listOf(2,1,2)
    }
    4 -> { // Snapshot a mutable list used as a hash-map key.
        val source = mutableListOf(1)
        val map = hashMapOf<List<Int>, String>()
        map[if (bad) source else source.toList()] = "value"
        source.add(2)
        map[listOf(1)] == "value"
    }
    5 -> (if (bad) "🙂".length else "🙂".codePointCount(0,"🙂".length)) == 1
    6 -> { // This contract rejects arithmetic overflow, rather than wrapping.
        val maximum = Int.MAX_VALUE
        try { if (bad) uncheckedIncrement(maximum) else Math.addExact(maximum,1); false }
        catch (_: ArithmeticException) { true }
    }
    7 -> { // Recover only the intended exception; cancellation must propagate.
        fun work() { if (bad) { try { throw InterruptedException("cancel") } catch (_: Exception) {} }
                     else throw InterruptedException("cancel") }
        try { work(); false } catch (_: InterruptedException) { true }
    }
    8 -> { // Model the two stale reads deterministically, without a data race.
        val count = AtomicInteger()
        if (bad) { val a=count.get(); val b=count.get(); count.set(a+1); count.set(b+1) }
        else { count.incrementAndGet(); count.incrementAndGet() }
        count.get() == 2
    }
    else -> error("topic must be 1..8")
}
private fun uncheckedIncrement(value: Int): Int = value + 1

fun main(args: Array<String>) {
    require(args.size == 2 && args[0] in setOf("red","green")) { "usage: red|green TOPIC" }
    val topic=args[1].toInt()
    val pass=contract(args[0]=="red",topic)
    println("CONTRACT topic $topic: ${if(pass) "PASS" else "FAIL"}")
    if (!pass) exitProcess(1)
}
