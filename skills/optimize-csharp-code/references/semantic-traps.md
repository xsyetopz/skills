# C# semantic traps

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| `ValueTask` misuse | Consumed twice, stored, combined, or returned from path without benefit. | Use `Task` unless measured and obey single-consumption/source lifetime. |
| Pooling ownership | Buffer returned while still referenced or not cleared when sensitive. | Define owner, lifetime, clear policy, exception/cancel cleanup. |
| Span escape | Ref-like data outlives stack/owner or crosses async boundary. | Use ref-safety rules and owned memory where needed. |
| Interop lifetime | Delegate/string/buffer freed or moved while native code retains it. | Define pin/root/ownership/callback and teardown. |
| Effective config mismatch | Project XML assumption differs after imports/conditions. | Inspect evaluated MSBuild and actual runtime/job. |

Also test the following domain partitions:

- effective target framework/runtime/JIT/AOT/GC/build properties.
- allocation, boxing, closure/state-machine, string and collection behavior.
- `Span<T>`/`Memory<T>` lifetime and ref-safety.
- async/cancellation/context, `Task` versus `ValueTask`, pooling and
  double-consumption.
- threading, memory model, locks/channels and disposal.
- P/Invoke marshalling, pinning, callbacks, native ownership and teardown.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
