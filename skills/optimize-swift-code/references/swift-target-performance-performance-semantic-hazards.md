# Performance semantic hazards for Swift Target Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Copy-on-write mutation | Shared storage unexpectedly copies or aliasing changes. | Test shared/unshared paths and inspect allocations. |
| Slice retention | Small slice retains large backing storage. | Copy at ownership boundary when retained memory matters. |
| Unsafe buffer escape | Pointer/reference outlives closure/storage. | Keep lifetime scoped and test under sanitizer where supported. |
| Actor bypass | Nonisolated/unsafe path introduces race. | Preserve isolation/Sendable and concurrency tests. |
| ARC micro-tuning | Ownership annotations applied without target/toolchain evidence. | Use Instruments and generated code for actual workload. |

Also test the following domain partitions:

- ARC retain/release and object lifetime.
- Array/String/Data copy-on-write, slices and retained storage.
- value/reference semantics, inout/exclusivity and unsafe buffers.
- throws/Result/optional behavior and cleanup.
- async/await, task cancellation, actor isolation and Sendable.
- generics/existentials/dynamic dispatch, ABI and deployment target.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
