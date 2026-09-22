# Performance semantic hazards for Scala Backend Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| View/laziness | Side effects, exceptions or repeated traversal change. | Test order/count/error and materialization boundaries. |
| Future context | Blocking or parallelism moves to wrong execution context. | Preserve scheduler/EC and cancellation/resource semantics. |
| Boxing folklore | Generic rewrite assumed allocation-free. | Inspect profile/bytecode for target Scala/JVM. |
| Collection type | Candidate changes ordering, duplicates or mutability. | Preserve collection contract. |
| Backend transfer | JVM benchmark claimed for JS/Native. | Measure selected backend only. |

Also test the following domain partitions:

- strict/lazy collections, views, iterators and repeated traversal.
- type erasure, boxing, specialization and generic dispatch.
- exceptions, `Option`/`Either`/effects and short-circuiting.
- Futures/execution contexts or effect runtime cancellation/resource behavior.
- implicit/given resolution, conversions and allocation.
- backend differences among JVM, Scala.js, Native.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
