fun main() {
    var calls = 0
    val values = sequenceOf(1, 2).onEach { calls++ }
    val actual = listOf(values.toList(), values.toList())
    println("actual=$actual calls=$calls")
    println("expected cached evaluation with calls=2")
    check(calls == 4)
}
