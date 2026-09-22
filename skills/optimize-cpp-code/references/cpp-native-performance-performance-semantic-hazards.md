# Performance semantic hazards for Cpp Native Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Dangling view | `string_view`/span/reference outlives source. | Prove owner lifetime and test mutation/reallocation boundaries. |
| Iterator invalidation | Container change invalidates cached iterator/reference. | Use documented invalidation rules and boundary tests. |
| Move semantics change | Moved-from object or exception guarantee differs. | Preserve documented postconditions and strong/basic guarantee. |
| Benchmark elision | Compiler removes or constant-folds work. | Use harness consumers/black-box and inspect generated code. |
| Allocator/ABI drift | Candidate changes allocator, layout, exceptions, RTTI or target flags. | Match environment or classify as a separate tradeoff. |

Also test the following domain partitions:

- object lifetime, ownership, RAII and move/copy behavior.
- iterator/reference/view invalidation and container complexity.
- exception guarantees, `noexcept`, error channels and cleanup.
- templates, inlining, virtual/type-erased dispatch, ABI and code size.
- data races, atomics, locks, memory order and task cancellation.
- floating-point rules and undefined behavior.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
