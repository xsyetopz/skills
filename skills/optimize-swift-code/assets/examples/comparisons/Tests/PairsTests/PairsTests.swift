import Testing
@testable import Pairs

@Test func differentialSmallDomain() {
    for length in 0...5 {
        var possibilities = 1
        for _ in 0..<length { possibilities *= 3 }
        for code in 0..<possibilities {
            var rest = code
            var values: [Int] = []
            for _ in 0..<length { values.append(rest % 3 - 1); rest /= 3 }
            let saved = values
            let strings = values.map(String.init)
            #expect(baselineAppend(values) == candidateAppend(values))
            #expect(baselineCounts(strings) == candidateCounts(strings))
            #expect(baselineCharacters(strings.joined()) == candidateCharacters(strings.joined()))
            #expect(baselineSum(values) == candidateSum(values))
            #expect(baselineQueue(values) == candidateQueue(values))
            let fields = strings.joined(separator: ":")
            #expect(baselineFieldLengths(fields) == candidateFieldLengths(fields))
            #expect(baselineReferenceStorage(values) == candidateContiguousValues(values))
            #expect(baselineAoS(values) == candidateSoA(values))
            #expect(values == saved)
        }
    }
}
@Test func expectedResultsUnicodeAndOwnership() {
    // Swift String equality is canonically equivalent: these spellings share a key.
    let unicode = ["é", "e\u{301}", "é", "🙂", "\0"]
    let expected = ["é": 3, "🙂": 1, "\0": 1]
    #expect(baselineCounts(unicode) == expected)
    #expect(candidateCounts(unicode) == expected)
    let text = "e\u{301}👩‍💻🇪🇪"
    let characters: [Character] = ["é", "👩‍💻", "🇪🇪"]
    #expect(baselineCharacters(text) == characters)
    #expect(candidateCharacters(text) == characters)
    #expect(baselineSum([-3, 2, 2, 0, 5]) == 8)
    #expect(candidateSum([-3, 2, 2, 0, 5]) == 8)
    #expect(baselineAppend([Int.min, Int.max]) == [Int.min, Int.max])
    #expect(candidateAppend([Int.min, Int.max]) == [Int.min, Int.max])
    #expect(baselineQueue([2, 1, 2]) == [2, 1, 2])
    #expect(candidateQueue([2, 1, 2]) == [2, 1, 2])
    #expect(baselineFieldLengths(":é::🙂:") == [0, 2, 0, 4, 0])
    #expect(candidateFieldLengths(":é::🙂:") == [0, 2, 0, 4, 0])
    #expect(baselineFieldLengths("") == [0])
    #expect(candidateFieldLengths("") == [0])
    // A combining mark after ':' belongs to that grapheme; do not swap this with a byte scan.
    #expect(baselineFieldLengths(":\u{301}") == candidateFieldLengths(":\u{301}"))
    var owner = [1, 2, 3]
    let slice = owner[1...]
    #expect(slice.startIndex == 1) // Not a zero-based Array.
    owner[1] = 9
    #expect(slice.first == 2) // Value semantics; no caller mutation leaks through.
}
