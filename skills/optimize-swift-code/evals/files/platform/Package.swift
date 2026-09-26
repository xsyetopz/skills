// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Geometry",
    platforms: [.macOS(.v13)],
    products: [.library(name: "Geometry", targets: ["Geometry"])],
    targets: [.target(name: "Geometry")]
)
