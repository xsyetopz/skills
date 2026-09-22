# Optimization regressions and recovery for Typescript Runtime Performance

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Benchmark mismatch** | Different input, compiler/runtime, flags, hardware, setup, or work is compared. | Match identities or state why comparison is invalid. |
| **Correctness sacrifice** | Validation, errors, ordering, cancellation, or work is removed. | Restore contract and use independent oracle. |
| **One-run confidence** | A single noisy result becomes a speedup claim. | Repeat, analyze variance, and inspect raw results. |
| **Profile-free tuning** | Technique chosen from folklore or syntax aesthetics. | Profile representative workload first. |
| **Debug/release conflation** | Debug or different optimization/target settings decide production performance. | Measure deployable configuration. |
| **Micro-to-system overreach** | Microbenchmark result becomes application/production claim. | Run component/end-to-end target metric. |
| **Tool maximalism** | Every profiler/benchmark is run without a decision question. | Use cheapest sufficient evidence path. |
| **Environment drift** | Candidate implicitly upgrades runtime/dependencies or uses native CPU flags. | Match or treat as separate authorized change. |
| **Type/runtime conflation** | Faster type check is claimed as runtime speed or vice versa. | Measure and report each pipeline separately. |
| **Type stripping** | Node/Bun execution of `.ts` is treated as `tsc` compatibility. | Run project compiler/type checks with exact tsconfig. |
| **Public type weakening** | Simpler types become `any`/broader and hide errors. | Preserve declaration/API contract and type tests. |
| **Incremental cache** | Warm stale cache makes build look fast or wrong. | Measure cold/warm explicitly and verify invalidation. |
| **Emit drift** | tsconfig/target change alters modules/helpers/runtime support. | Inspect emitted/package outputs and consumers. |

## Recovery discipline

Preserve the first observable TypeScript optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the TypeScript optimization appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
