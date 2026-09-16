let owner = Array(0..<4)
let actual = owner[2...]
print("actual startIndex=\(actual.startIndex)")
print("expected zero-based independent Array")
precondition(actual.startIndex == 2)
