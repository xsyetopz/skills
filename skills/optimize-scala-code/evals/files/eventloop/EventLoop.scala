package eventloop

final case class State(tick: Long, queue: Vector[Int])

object EventLoop:
  /** Test instrumentation only (not exported): how many times render ran. */
  var renders = 0L

  def render(s: State): String =
    renders += 1
    s"tick=${s.tick} depth=${s.queue.size} head=${s.queue.headOption.getOrElse(-1)}"

  def step(s: State, event: Int, log: Logger): State =
    log.debug(s"state=${render(s)} event=$event")
    State(s.tick + 1, if event % 3 == 0 then s.queue.drop(1) else s.queue :+ event)

  def run(events: Array[Int], log: Logger): State =
    var s = State(0, Vector.empty)
    var i = 0
    while i < events.length do
      s = step(s, events(i), log)
      i += 1
    s
