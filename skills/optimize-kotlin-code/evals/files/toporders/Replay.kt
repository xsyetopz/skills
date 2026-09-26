package toporders

// Replays the dashboard workload:
//   kotlinc toporders/*.kt -include-runtime -d replay.jar && java -cp replay.jar toporders.ReplayKt
fun main() {
    val orders = List(200_000) { i -> Order(id = 1_000_000L + i, total = (i * 37) % 250) }
    var sink = 0L
    val start = System.nanoTime()
    repeat(2_000) { sink += topIds(orders, 20).sum() }
    println("sink=$sink elapsed=${(System.nanoTime() - start) / 1_000_000} ms")
}
