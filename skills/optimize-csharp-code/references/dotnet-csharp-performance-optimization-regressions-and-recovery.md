# Optimization regressions and recovery for Dotnet Csharp Performance

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
| **`ValueTask` misuse** | Consumed twice, stored, combined, or returned from path without benefit. | Use `Task` unless measured and obey single-consumption/source lifetime. |
| **Pooling ownership** | Buffer returned while still referenced or not cleared when sensitive. | Define owner, lifetime, clear policy, exception/cancel cleanup. |
| **Span escape** | Ref-like data outlives stack/owner or crosses async boundary. | Use ref-safety rules and owned memory where needed. |
| **Interop lifetime** | Delegate/string/buffer freed or moved while native code retains it. | Define pin/root/ownership/callback and teardown. |
| **Effective config mismatch** | Project XML assumption differs after imports/conditions. | Inspect evaluated MSBuild and actual runtime/job. |

## Recovery discipline

Preserve the first observable C#/.NET optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the C#/.NET optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
