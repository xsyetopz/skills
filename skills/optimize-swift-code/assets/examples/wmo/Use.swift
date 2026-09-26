@inline(never)
public func countAll(_ values: [Int]) -> Int {
  let counter = Counter()
  for v in values { counter.bump(v) }
  return counter.count
}

@inline(never)
public func sumAll(_ values: [Int]) -> Int {
  sumMapped(values) { $0 &* 2 }
}
