package eventloop

final class Logger(var enabled: Boolean, sink: String => Unit):
  def debug(msg: String): Unit = if enabled then sink(msg)
