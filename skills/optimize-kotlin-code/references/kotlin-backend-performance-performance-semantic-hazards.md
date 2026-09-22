# Performance semantic hazards for Kotlin Backend Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Sequence regression | Small pipeline gets slower or changes exception timing/laziness. | Benchmark representative sizes and test side-effect/order semantics. |
| Coroutine leak | `GlobalScope`/unowned jobs outlive component. | Use structured scope and explicit cancellation/join. |
| Cancellation swallowed | Broad catch converts cancellation to success. | Rethrow/preserve cancellation according to API. |
| Boxing surprise | Value class/generic/interface path still boxes. | Inspect bytecode/profile for target backend. |
| Backend conflation | JVM evidence claimed for Native/JS. | Test and document selected backend only. |

Also test the following domain partitions:

- backend and compiler/plugin configuration.
- nullability, exceptions, inline/value classes and boxing.
- collections/sequences/lazy evaluation and iteration order.
- coroutines, structured concurrency, cancellation, context and dispatchers.
- Java interop/platform types and SAM/reflection behavior.
- Kotlin/Native ownership/memory or JS runtime semantics when selected.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
