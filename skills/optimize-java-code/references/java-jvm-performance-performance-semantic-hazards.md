# Performance semantic hazards for Java JVM Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| JMH dead code | Result is unused or constant-folded. | Return/consume result and vary realistic inputs; inspect generated work. |
| Warmup mismatch | Candidate appears fast due to tiering/profile state. | Use forks/warmup and report startup separately. |
| Stream rewrite | Ordering, short-circuiting, exceptions or boxing changes. | Test semantic partitions and profile actual pipeline. |
| Unsafe publication | Lock removal exposes partially initialized/stale state. | Preserve JMM happens-before and concurrency tests. |
| JVM flag tuning | Benchmark uses flags not deployable or matched. | Record and match actual runtime/container limits. |

Also test the following domain partitions:

- JMM happens-before, synchronization, volatile/atomics and safe publication.
- exceptions, ordering, null behavior and API compatibility.
- boxing, streams/lambdas, collections and allocation.
- JIT tiering, deoptimization, escape analysis and dead-code elimination.
- GC/heap/reference retention and classloader lifetime.
- reflection, modules, serialization and deployment/JDK compatibility.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
