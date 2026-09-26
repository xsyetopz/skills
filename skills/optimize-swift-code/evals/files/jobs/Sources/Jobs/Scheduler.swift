public struct Job: Equatable, Sendable {
    public let id: Int
    public let cost: Int
    public init(id: Int, cost: Int) {
        self.id = id
        self.cost = cost
    }
}

/// Returns job ids in the order they run. A job costing more than `limit`
/// is split into two halves that go to the back of the queue.
public func schedule(_ jobs: [Job], limit: Int) -> [Int] {
    var queue = jobs
    var order: [Int] = []
    while !queue.isEmpty {
        let job = queue.removeFirst()
        if job.cost > limit {
            queue.append(Job(id: job.id, cost: job.cost / 2))
            queue.append(Job(id: job.id, cost: job.cost - job.cost / 2))
        } else {
            order.append(job.id)
        }
    }
    return order
}
