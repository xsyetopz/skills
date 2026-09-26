import Importer

// Stand-in for the importer: 2 million lines in production.
let lines = (0..<200_000).map { i in
    "2026-09-01T10:00:\(i % 60)Z,billing-service-eu-west-\(i % 7),\(i % 13 == 0 ? "ERROR" : "INFO"),request finished after retry,\(i)"
}
let clock = ContinuousClock()
var stats = ImportStats()
let elapsed = clock.measure { stats = importStats(lines) }
print(stats, elapsed)
