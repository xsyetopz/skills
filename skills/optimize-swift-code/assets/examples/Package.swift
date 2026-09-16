// swift-tools-version: 6.0
import PackageDescription
let package = Package(
    name: "SwiftOptimizationExamples",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "Pairs", targets: ["Pairs"]),
        .executable(name: "pairs-cli", targets: ["PairsCLI"]),
    ],
    targets: [
        .target(name: "Pairs", path: "comparisons/Sources/Pairs"),
        .executableTarget(
            name: "PairsCLI",
            dependencies: ["Pairs"],
            path: "comparisons/Sources/PairsCLI"
        ),
        .executableTarget(name: "Semantics", path: "correctness"),
        .testTarget(
            name: "PairsTests",
            dependencies: ["Pairs"],
            path: "comparisons/Tests/PairsTests"
        ),
    ],
    swiftLanguageModes: [.v6]
)
