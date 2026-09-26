// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "Importer",
    platforms: [.macOS(.v14)],
    targets: [
        .target(name: "Importer"),
        .executableTarget(name: "importer-cli", dependencies: ["Importer"]),
    ]
)
