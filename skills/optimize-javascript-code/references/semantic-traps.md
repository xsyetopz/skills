# JavaScript semantic traps

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Async equivalence | Parallel Promise rewrite changes ordering, concurrency limit or rejection timing. | Specify and test ordering/cancellation/error aggregation. |
| Event-loop blocking | CPU optimization still monopolizes UI/server loop. | Measure long tasks/tail latency and chunk/offload appropriately. |
| Runtime transfer | Node result is claimed for browser/Bun/Deno. | Measure exact runtime/version and APIs. |
| JIT folklore | Code is rewritten for remembered V8 optimization behavior. | Use current profiler/deopt evidence and prefer clear semantics. |
| Buffer/view alias | Candidate mutates shared backing data or changes copy semantics. | Test aliasing/detachment and ownership. |

Also test the following domain partitions:

- coercion, `NaN`, `-0`, BigInt, Unicode and property access.
- object identity, prototypes, getters/setters and enumeration order.
- Promises, microtasks/macrotasks, cancellation/AbortSignal and event-loop
  fairness.
- exceptions/rejections, stack and async context.
- typed arrays/buffer views, detachment and shared memory.
- runtime/browser/Node API and module-format compatibility.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
