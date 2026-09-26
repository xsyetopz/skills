// swift-tools-version: 6.1
// Construct catalog for the optimize-swift-code skill. Build it only through
// ../verify.sh, which copies it to a temporary directory first.
import PackageDescription

let package = Package(
  name: "SwiftConstructs",
  platforms: [.macOS(.v15)],
  products: [
    .library(name: "Constructs", targets: ["Constructs"])
  ],
  targets: [
    // Allocation and ARC counters (Darwin only): see CCount/ccount.c.
    .target(name: "CCount"),
    // Separate module for the @inlinable / cross-module cards.
    .target(name: "Helper"),
    .target(name: "Constructs", dependencies: ["Helper"]),
    .executableTarget(
      name: "Catalog",
      dependencies: ["Constructs", "CCount"]
    ),
  ],
  swiftLanguageModes: [.v6]
)
