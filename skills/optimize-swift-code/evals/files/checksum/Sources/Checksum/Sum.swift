/// Sum of all values. Traps on overflow: an overflowing batch means corrupt
/// input upstream and must crash rather than produce a wrong total.
public func total(_ values: [Int]) -> Int {
    var sum = 0
    for i in 0..<values.count {
        sum += values[i]
    }
    return sum
}
