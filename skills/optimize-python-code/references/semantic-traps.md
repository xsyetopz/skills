# Python semantic traps

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Iterator exhaustion | Candidate consumes iterable twice or changes lazy timing. | Test one-shot iterators and side effects. |
| Falsy/default conflation | `x or default` changes valid 0/empty/False values. | Use explicit sentinel/None contract. |
| Exception swallowing | Fast path returns default instead of required error. | Preserve exception type/context and cleanup. |
| Benchmark import/setup | Different setup or environment is timed. | Use pyperf metadata/process isolation and same work. |
| C-extension/GIL assumption | Threading change relies on release/GIL behavior not true for target build. | Inspect extension/runtime/free-threaded support. |

Also test the following domain partitions:

- iterator/generator one-shot consumption and laziness.
- truthiness, equality/identity, hashing, ordering, Unicode and numeric
  behavior.
- exceptions/warnings/context manager cleanup and resource lifetime.
- mutability/aliasing/copying and retained objects.
- GIL/free-threaded build/C-extension thread safety.
- descriptor/property/import/module and supported-version behavior.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
