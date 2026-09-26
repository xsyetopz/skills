import Foundation

public let publicConstant = 1
internal let moduleConstant = 2
private let fileConstant = 3

public final class PublicType {
    public init() {}

    public func publicMethod() {}

    internal func moduleMethod() {}

    fileprivate func fileMethod() {}

    private func privateMethod() {}
}

private struct PrivateType {
    func helper() {}
}
