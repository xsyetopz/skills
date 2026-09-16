import Pairs
struct UsageError: Error {}
@main
struct Main {
    static func main() throws {
        let args = Array(CommandLine.arguments.dropFirst())
        guard args.count == 3, ["baseline", "candidate"].contains(args[0]),
              let which = Int(args[1]), let size = Int(args[2]),
              (0...100_000).contains(size) else { throw UsageError() }
        let values = (0..<size).map { $0 % 31 - 15 }
        let strings = values.map(String.init)
        let candidate = args[0] == "candidate"
        switch which {
        case 1: print(candidate ? candidateAppend(values) : baselineAppend(values))
        case 2:
            let counts = candidate ? candidateCounts(strings) : baselineCounts(strings)
            print(counts.keys.sorted().map { key in "\(key):\(counts[key, default: 0])" })
        case 3:
            let text = strings.joined()
            print(candidate ? candidateCharacters(text) : baselineCharacters(text))
        case 4: print(candidate ? candidateSum(values) : baselineSum(values))
        case 5: print(candidate ? candidateQueue(values) : baselineQueue(values))
        case 6:
            let text = strings.joined(separator: ":")
            print(candidate ? candidateFieldLengths(text) : baselineFieldLengths(text))
        case 7: print(candidate ? candidateContiguousValues(values) : baselineReferenceStorage(values))
        case 8: print(candidate ? candidateSoA(values) : baselineAoS(values))
        default: throw UsageError()
        }
    }
}
