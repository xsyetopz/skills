# Rust semantic traps

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Clone removal | Borrow keeps huge owner alive or changes API lifetime. | Measure retained memory and prove owner lifetime. |
| Iterator semantics | Eager/lazy rewrite changes side effects/errors/order. | Test one-shot and error paths. |
| Unsafe fast path | Validity/provenance/alignment/tail invariant is only commented. | Enforce safe boundary and run differential/Miri/sanitizer where supported. |
| Async cancellation | Optimization moves resource cleanup past cancellation/drop. | Test cancellation at await points and drop behavior. |
| CPU target | Native features produce artifact incompatible with supported fleet. | Use dispatch/fallback or approved deployment target. |

Also test the following domain partitions:

- ownership/borrowing/lifetime/drop order and aliasing.
- clone/copy/reference-counting and retained ownership.
- iterators/laziness/order/errors and panic behavior.
- unsafe validity, alignment, initialization, provenance and bounds.
- async cancellation/drop, Send/Sync, pinning and backpressure.
- atomics/locks/memory order, target features and fallback dispatch.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
