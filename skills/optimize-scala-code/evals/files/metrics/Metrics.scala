package metrics

object Metrics:
  /** Called once per scrape for every histogram; latencies are in nanoseconds. */
  def totalLatency(samples: Array[Long]): Long = Stats.sum(samples)
