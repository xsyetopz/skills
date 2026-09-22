# Optimization regressions and recovery for Swift Target Performance

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
| **Copy-on-write mutation** | Shared storage unexpectedly copies or aliasing changes. | Test shared/unshared paths and inspect allocations. |
| **Slice retention** | Small slice retains large backing storage. | Copy at ownership boundary when retained memory matters. |
| **Unsafe buffer escape** | Pointer/reference outlives closure/storage. | Keep lifetime scoped and test under sanitizer where supported. |
| **Actor bypass** | Nonisolated/unsafe path introduces race. | Preserve isolation/Sendable and concurrency tests. |
| **ARC micro-tuning** | Ownership annotations applied without target/toolchain evidence. | Use Instruments and generated code for actual workload. |

## Recovery discipline

Preserve the first observable Swift optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Swift optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
