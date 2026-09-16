public func baselineAppend(_ values: [Int]) -> [Int] {
    values.reduce([]) { $0 + [$1] }
}
public func candidateAppend(_ values: [Int]) -> [Int] {
    values.reduce(into: []) { $0.append($1) }
}
public func baselineCounts(_ values: [String]) -> [String: Int] {
    Dictionary(grouping: values, by: { $0 }).mapValues { $0.count }
}
public func candidateCounts(_ values: [String]) -> [String: Int] {
    values.reduce(into: [:]) { $0[$1, default: 0] += 1 }
}
public func baselineCharacters(_ text: String) -> [Character] {
    var result: [Character] = []
    for offset in 0..<text.count {
        result.append(text[text.index(text.startIndex, offsetBy: offset)])
    }
    return result
}
public func candidateCharacters(_ text: String) -> [Character] {
    var result: [Character] = []
    for character in text { result.append(character) }
    return result
}
public func baselineSum(_ values: [Int]) -> Int {
    values.filter { $0.isMultiple(of: 2) }.map { $0 * $0 }.reduce(0, +)
}
public func candidateSum(_ values: [Int]) -> Int {
    var result = 0
    for value in values where value.isMultiple(of: 2) { result += value * value }
    return result
}
public func baselineQueue(_ values: [Int]) -> [Int] {
    var pending = values
    var result: [Int] = []
    while !pending.isEmpty { result.append(pending.removeFirst()) }
    return result
}
public func candidateQueue(_ values: [Int]) -> [Int] {
    var pending = values[...]
    var result: [Int] = []
    while let value = pending.popFirst() { result.append(value) }
    return result
}
public func baselineFieldLengths(_ text: String) -> [Int] {
    text.split(separator: ":", omittingEmptySubsequences: false)
        .map(String.init).map { $0.utf8.count }
}
public func candidateFieldLengths(_ text: String) -> [Int] {
    text.split(separator: ":", omittingEmptySubsequences: false)
        .map { $0.utf8.count }
}
private final class ReferencePoint {
    let x: Int
    let y: Int
    init(x: Int, y: Int) { self.x = x; self.y = y }
}
private struct ValuePoint { let x: Int; let y: Int }
public func baselineReferenceStorage(_ values: [Int]) -> Int {
    let points = values.enumerated().map { ReferencePoint(x: $0.element, y: $0.offset) }
    return points.reduce(0) { $0 + $1.x + $1.y }
}
public func candidateContiguousValues(_ values: [Int]) -> Int {
    let points = ContiguousArray(values.enumerated().map { ValuePoint(x: $0.element, y: $0.offset) })
    return points.reduce(0) { $0 + $1.x + $1.y }
}
private struct Record { let x: Double; let y: Double }
private struct Records { let x: [Double]; let y: [Double] }
public func baselineAoS(_ values: [Int]) -> Double {
    let records = values.enumerated().map { Record(x: Double($0.element), y: Double($0.offset)) }
    _ = records.reduce(0) { $0 + $1.y }
    return records.reduce(0) { $0 + $1.x }
}
public func candidateSoA(_ values: [Int]) -> Double {
    let records = Records(x: values.map(Double.init), y: values.indices.map(Double.init))
    _ = records.y.reduce(0, +)
    return records.x.reduce(0, +)
}
