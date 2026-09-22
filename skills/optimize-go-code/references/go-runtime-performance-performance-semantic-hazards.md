# Performance semantic hazards for Go Runtime Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Slice retention | Small view retains huge backing array. | Copy at ownership boundary when retained-memory profile justifies it. |
| Goroutine leak | Optimization spawns work without cancel/join/drain. | Define owner, context, channel close, and terminal wait. |
| Pool state leak | Reused object carries sensitive/stale state or escapes after Put. | Reset, define ownership, and never use after Put. |
| Map order | Candidate relies on iteration order. | Sort when contract requires order and benchmark that contract. |
| Benchmark setup | Input allocation/setup is timed inconsistently. | Place setup according to measured operation and document it. |

Also test the following domain partitions:

- slice/map/string aliasing and backing-array retention.
- interface boxing/dynamic dispatch and escape to heap.
- goroutine ownership, cancellation, channel closure and leaks.
- sync/atomic/locks/memory model and data races.
- error identity/wrapping, defer/recover and cleanup.
- map iteration order, Unicode/rune versus byte behavior.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
