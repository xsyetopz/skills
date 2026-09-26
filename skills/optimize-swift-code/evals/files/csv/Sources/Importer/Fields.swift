/// Splits one CSV line (the exporter never quotes) into its fields.
/// Empty fields are kept: "a,,b" has three fields.
public func fields(_ line: String) -> [String] {
    line.split(separator: ",", omittingEmptySubsequences: false).map { String($0) }
}

public struct ImportStats: Equatable, Sendable {
    public var rows = 0
    public var errors = 0
    public var wide = 0

    public init() {}
}

/// Every caller in the app goes through here; it only counts fields and
/// compares them to constants.
public func importStats(_ lines: [String]) -> ImportStats {
    var stats = ImportStats()
    for line in lines {
        let f = fields(line)
        stats.rows += 1
        if f.count > 4 { stats.wide += 1 }
        if f.count > 2 && f[2] == "ERROR" { stats.errors += 1 }
    }
    return stats
}
