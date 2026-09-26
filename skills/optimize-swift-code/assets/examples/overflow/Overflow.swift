// Checked arithmetic: -O keeps the overflow trap, -Ounchecked removes it
// and the result is undefined. Run through ../verify.sh build.
@inline(never)
func addAll(_ values: [Int]) -> Int {
  var total = 0
  for v in values { total += v }
  return total
}

// argv decides the input, so the optimizer cannot fold the overflow away.
let big = CommandLine.arguments.count > 1 ? Int.max : 1
print(addAll([big, 1]))
