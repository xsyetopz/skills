// Internal class with no subclass anywhere in the module.
class Counter {
  var count = 0
  func bump(_ by: Int) { count &+= by }
}

// Generic helper defined in another file than its caller.
func sumMapped<T>(_ xs: [T], _ f: (T) -> Int) -> Int {
  var total = 0
  for x in xs { total &+= f(x) }
  return total
}
