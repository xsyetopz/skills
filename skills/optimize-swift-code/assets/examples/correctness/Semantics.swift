import Foundation
private final class Box { var value: Int; init(_ value: Int) { self.value=value } }

private func contract(_ bad: Bool, _ topic: Int) async -> Bool {
    switch topic {
    case 1: // Slice indices are not rebased: an API promising zero-based indices copies.
        let slice=Array(0..<4)[2...]
        return (bad ? slice.startIndex : Array(slice).startIndex)==0
    case 2: // Count extended grapheme clusters, not UTF-8 bytes, in this API.
        return (bad ? "🙂".utf8.count : "🙂".count)==1
    case 3: // Snapshot a reference value, rather than assigning another reference.
        let owner=Box(1)
        let snapshot=bad ? owner : Box(owner.value)
        owner.value=2
        return snapshot.value==1
    case 4: // Checked arithmetic must report overflow, not silently wrap it.
        let value=Int.max
        let result=value.addingReportingOverflow(1)
        let accepted=bad ? Optional(value &+ 1) : (result.overflow ? nil : result.partialValue)
        return accepted==nil
    case 5: // Preserve duplicate elements in the requested result sequence.
        let values=[2,1,2]
        return (bad ? Array(Set(values)) : values)==[2,1,2]
    case 6: // Zero is a valid explicitly supplied setting, not a missing default.
        let setting: Int?=0
        let value=bad ? ((setting ?? 0)==0 ? 10 : setting!) : (setting ?? 10)
        return value==0
    case 7: // Self-cancel a child before its cancellation check: no scheduling race.
        let task=Task { () throws -> Bool in
            withUnsafeCurrentTask { $0?.cancel() }
            do { try Task.checkCancellation(); return true }
            catch { if bad { return true }; throw error }
        }
        do { _=try await task.value; return false }
        catch is CancellationError { return true }
        catch { return false }
    case 8: // Sequential idempotence of completion; not a thread-safety proof.
        var completed=false
        var callbacks=0
        func finish() { if !bad && completed { return }; completed=true; callbacks += 1 }
        finish();finish()
        return callbacks==1
    default: fatalError("topic must be 1..8")
    }
}
@main struct Semantics {
    static func main() async {
        let args=Array(CommandLine.arguments.dropFirst())
        precondition(args.count==2 && ["red","green"].contains(args[0]),"usage: red|green TOPIC")
        let topic=Int(args[1])!
        let pass=await contract(args[0]=="red",topic)
        print("CONTRACT topic \(topic): \(pass ? "PASS" : "FAIL")")
        if !pass { exit(1) }
    }
}
