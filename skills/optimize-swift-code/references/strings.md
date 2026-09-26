# String constructs

Native Swift strings store UTF-8 ([UTF-8 String blog][utf8-blog]). A
`Character` is an extended grapheme cluster, so `Character` iteration
runs grapheme segmentation while `utf8` iteration reads bytes. Each card
states which of the two its result depends on. Pairs live in
`assets/examples/constructs/Sources/Constructs/Strings.swift`. Counts come
from `sh assets/examples/verify.sh verify` and times from `sh verify.sh
time` (shared Apple M1 Max, Swift 6.3.3, `-O -wmo`; machine-specific).

## Contents

- UTF-8 view instead of Character iteration
- Substring instead of String copies
- Iteration instead of index offsetBy
- String reserveCapacity
- Small strings

## UTF-8 view instead of Character iteration

**Definition.** `for b in text.utf8` visits UTF-8 code units (`UInt8`)
of the string's native storage. `for c in text` produces `Character`s,
which requires finding grapheme-cluster boundaries.

**Use when.**

- The scan looks for ASCII delimiters or bytes (`,`, `\n`, `:`) and the
  profile shows `String.Iterator.next` or grapheme-breaking frames.

**Do not use when.**

- The result must respect grapheme clusters: a combining mark after a
  delimiter joins it into one `Character`. `",\u{301}x"` has 0
  `Character`s equal to `","` but 1 comma byte, and the oracle asserts
  that difference. Likewise `"\r\n"` is one `Character`.
- The string can be a lazily bridged `NSString` that is not contiguous
  UTF-8 (`isContiguousUTF8 == false`): call `makeContiguousUTF8()` or the
  mutating `withUTF8 { }` once before the loop ([SE-0247][se247]).

**Example.** Runnable: `Strings.swift` (`countCommasUTF8`).

```swift
@inline(never)
public func countCommasUTF8(_ text: String) -> Int {
    var n = 0
    for b in text.utf8 where b == UInt8(ascii: ",") { n += 1 }
    return n
}
```

**Cost removed.** Grapheme segmentation per character. Measured, 4,608-byte
string: 44491.9 ns -> 6917.3 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal counts for `""`, `","`,
   `"a,b"`, accented and emoji text, `"\r\n,"`, plus the asserted
   difference on `",\u{301}x"`.
1. `sh assets/examples/verify.sh time utf8`.

## Substring instead of String copies

**Definition.** `split` returns `Substring`s that share the original
storage. `String(substring)` copies the bytes into new storage (inline
for up to 15 UTF-8 bytes; see [Small strings](#small-strings)). A
function that accepts `Substring` or `some StringProtocol` avoids the
copy.

**Use when.**

- Parsing code maps split fields to `String` only to read them (count,
  compare, convert to numbers) within the same scope.

**Do not use when.**

- The fields are stored long-term: a `Substring` keeps the whole input
  string alive ([Substring.swift][substring-src]). Copy at that
  boundary.
- An API requires `String` and cannot be changed.

**Example.** Runnable: `Strings.swift` (`fieldByteCountsSubstring`).

```swift
@inline(never)
public func fieldByteCountsSubstring(_ line: String) -> [Int] {
    line.split(separator: ",", omittingEmptySubsequences: false)
        .map { $0.utf8.count }
}
```

**Cost removed.** One allocation per field longer than 15 bytes plus the
intermediate `[String]`. Measured: `ALLOC Substring (fields > 15 bytes):
1013 -> 12` (1,000 fields); with fields of at most 15 bytes only the
intermediate array differs: `13 -> 12`. package-benchmark, 256 long
fields: `Malloc (total)` 267 -> 10, `Retains` 513 -> 257, p50 123 µs ->
101 µs.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal counts for long, short,
   and empty lines, plus both `ALLOC` lines.
1. `BENCH_FILTER='Substring.*' sh assets/examples/verify.sh measure`.

## Iteration instead of index offsetBy

**Definition.** `String.Index` is not an integer offset:
`text.index(text.startIndex, offsetBy: k)` walks `k` characters, so
indexing by offset inside a loop is O(n²). Iterating (or advancing one
index) is O(n).

**Use when.**

- Code loops `for i in 0..<text.count` and indexes with
  `index(_:offsetBy:)`, or calls `text.count` repeatedly.

**Do not use when.**

- Code needs repeated random access: convert once to `Array(text)` (or
  `Array(text.utf8)` for bytes) and index the array.

**Example.** Runnable: `Strings.swift` (`charactersIterating`).

```swift
@inline(never)
public func charactersIterating(_ text: String) -> [Character] {
    var out: [Character] = []
    for c in text { out.append(c) }
    return out
}
```

**Cost removed.** Quadratic index walking. Measured, 512 characters:
328156.3 ns -> 4883.4 ns.

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal characters for
   `"e\u{301}👩‍💻🇪🇪" + ...` (combining mark, ZWJ emoji, flag) and `""`.

## String reserveCapacity

**Definition.** `String.reserveCapacity(n)` reserves room for `n` UTF-8
code units, so repeated `+=` appends do not reallocate.

**Use when.**

- A string is built by appending many parts whose total byte length is
  known or cheap to compute.

**Do not use when.**

- The parts are few, or the total is unknown and computing it costs a
  pass over the parts.
- `joined(separator:)` or string interpolation expresses the same
  result directly.

**Example.** Runnable: `Strings.swift` (`joinReserved`).

```swift
@inline(never)
public func joinReserved(_ parts: [String]) -> String {
    var out = ""
    out.reserveCapacity(parts.reduce(0) { $0 + $1.utf8.count })
    for p in parts { out += p }
    return out
}
```

**Cost removed.** Growth reallocations. Measured: `ALLOC
String.reserveCapacity: 9 -> 1` (1,000 parts).

**Verify.**

1. `sh assets/examples/verify.sh verify`: equal strings and the `ALLOC`
   line.

## Small strings

**Definition.** On 64-bit platforms a string of up to 15 UTF-8 code
units is stored inline in the `String` value itself, with no heap
allocation ([UTF-8 String blog][utf8-blog]).

**Use when.**

- Designing hot keys, tags, or identifiers: at 15 UTF-8 bytes or fewer
  they avoid an allocation per created string.
- Explaining why a `String`-copy change shows no allocation difference:
  short fields are already inline.

**Do not use when.**

- Truncating or re-encoding data to fit the limit changes its meaning.
- 32-bit targets: the blog gives 10 code units there.

**Example.** Runnable: `Strings.swift` (`makeString`).

```swift
@inline(never)
public func makeString(repeating unit: Character, count: Int) -> String {
    String(repeating: unit, count: count)
}
```

**Cost removed.** One heap allocation per string. Measured: `ALLOC small
string 15 -> 16 bytes: 0 -> 1`.

**Verify.**

1. `sh assets/examples/verify.sh verify`: asserts 0 allocations at 15
   bytes and 1 at 16.

[utf8-blog]: https://www.swift.org/blog/utf8-string/
[substring-src]: https://github.com/swiftlang/swift/blob/main/stdlib/public/core/Substring.swift
[se247]: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0247-contiguous-strings.md
