public struct Vector2: Equatable, Sendable {
    public var x: Double
    public var y: Double

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    public var length: Double { (x * x + y * y).squareRoot() }
}
