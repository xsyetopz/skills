// swift-tools-version: 6.1
// package-benchmark harness for the construct catalog. Run it through
// ../verify.sh measure; it fetches package-benchmark pinned by
// Package.resolved.
import PackageDescription

let package = Package(
  name: "ConstructBenchmarks",
  platforms: [.macOS(.v15)],
  dependencies: [
    .package(
      url: "https://github.com/ordo-one/package-benchmark",
      exact: "1.36.2"
    ),
    .package(path: "../constructs"),
  ],
  targets: [
    .executableTarget(
      name: "Pairs",
      dependencies: [
        .product(name: "Benchmark", package: "package-benchmark"),
        .product(name: "Constructs", package: "constructs"),
      ],
      path: "Benchmarks/Pairs",
      plugins: [
        .plugin(name: "BenchmarkPlugin", package: "package-benchmark")
      ]
    )
  ]
)
