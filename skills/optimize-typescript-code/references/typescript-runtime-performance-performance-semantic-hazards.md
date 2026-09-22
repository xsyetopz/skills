# Performance semantic hazards for Typescript Runtime Performance

Performance work is incorrect when it changes a supported result, error,
ownership/lifetime, ordering, concurrency, cancellation, ABI/API, serialization,
or target condition without an authorized contract change.

| Trap | Typical false optimization | Required check |
| --- | --- | --- |
| Type/runtime conflation | Faster type check is claimed as runtime speed or vice versa. | Measure and report each pipeline separately. |
| Type stripping | Node/Bun execution of `.ts` is treated as `tsc` compatibility. | Run project compiler/type checks with exact tsconfig. |
| Public type weakening | Simpler types become `any`/broader and hide errors. | Preserve declaration/API contract and type tests. |
| Incremental cache | Warm stale cache makes build look fast or wrong. | Measure cold/warm explicitly and verify invalidation. |
| Emit drift | tsconfig/target change alters modules/helpers/runtime support. | Inspect emitted/package outputs and consumers. |

Also test the following domain partitions:

- TypeScript erasure versus emitted JavaScript behavior.
- tsconfig/module/target/downlevel helpers and bundler transformations.
- type inference/generic/conditional-type complexity and public declaration API.
- JavaScript coercion, async ordering, errors, objects and buffers.
- incremental build/cache/project references and generated declarations.
- source-map/profile attribution and runtime-specific APIs.

Use sanitizers, race tools, Miri, type checkers, or static analyzers only for
the properties they can establish. Their success is not a substitute for runtime
contract tests or matched performance measurement.
