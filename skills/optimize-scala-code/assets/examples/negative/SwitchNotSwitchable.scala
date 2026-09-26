//> using scala 3.8.4
//> using options -Werror
// Must fail with -Werror: the JVM has no switch instruction for Long, so
// @switch reports E115 "Could not emit switch for @switch annotated match".
import scala.annotation.switch

def classify(n: Long): Int = (n: @switch) match
  case 1L => 10
  case 2L => 20
  case 3L => 30
  case _  => -1
