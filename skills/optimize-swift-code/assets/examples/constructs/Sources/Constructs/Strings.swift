// String constructs: UTF-8 view scans, Substring, offset indexing, small
// strings, capacity.

// MARK: utf8 view instead of Character iteration

@inline(never)
public func countCommasCharacters(_ text: String) -> Int {
  var n = 0
  for c in text where c == "," { n += 1 }
  return n
}

@inline(never)
public func countCommasUTF8(_ text: String) -> Int {
  var n = 0
  for b in text.utf8 where b == UInt8(ascii: ",") { n += 1 }
  return n
}

// MARK: Substring instead of String copies

@inline(never)
public func fieldByteCountsCopying(_ line: String) -> [Int] {
  line.split(separator: ",", omittingEmptySubsequences: false)
    .map { String($0) }
    .map { $0.utf8.count }
}

@inline(never)
public func fieldByteCountsSubstring(_ line: String) -> [Int] {
  line.split(separator: ",", omittingEmptySubsequences: false)
    .map { $0.utf8.count }
}

// MARK: iterate instead of index(offsetBy:)

@inline(never)
public func charactersByOffset(_ text: String) -> [Character] {
  var out: [Character] = []
  for offset in 0..<text.count {
    out.append(text[text.index(text.startIndex, offsetBy: offset)])
  }
  return out
}

@inline(never)
public func charactersIterating(_ text: String) -> [Character] {
  var out: [Character] = []
  for c in text { out.append(c) }
  return out
}

// MARK: String.reserveCapacity

@inline(never)
public func joinGrowing(_ parts: [String]) -> String {
  var out = ""
  for p in parts { out += p }
  return out
}

@inline(never)
public func joinReserved(_ parts: [String]) -> String {
  var out = ""
  out.reserveCapacity(parts.reduce(0) { $0 + $1.utf8.count })
  for p in parts { out += p }
  return out
}

// MARK: small strings (up to 15 UTF-8 code units inline on 64-bit)

@inline(never)
public func makeString(repeating unit: Character, count: Int) -> String {
  String(repeating: unit, count: count)
}
