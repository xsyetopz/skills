//> using scala 3.8.4
// Must fail to compile: the recursive call is not in tail position.
import scala.annotation.tailrec

@tailrec def sum(n: Int): Long = if n == 0 then 0L else n + sum(n - 1)
