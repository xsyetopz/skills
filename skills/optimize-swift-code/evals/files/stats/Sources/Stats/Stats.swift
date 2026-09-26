/// Running totals shared by every ingestion task.
public actor Stats {
    public private(set) var total = 0
    public private(set) var count = 0

    public init() {}

    public func add(_ value: Int) {
        total += value
        count += 1
    }
}

/// Called by each ingestion task with a batch of about 100k values.
public func record(_ values: [Int], into stats: Stats) async {
    for value in values {
        await stats.add(value)
    }
}
