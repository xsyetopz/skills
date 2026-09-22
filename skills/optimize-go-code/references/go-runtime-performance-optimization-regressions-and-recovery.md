# Optimization regressions and recovery for Go Runtime Performance

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
| **Slice retention** | Small view retains huge backing array. | Copy at ownership boundary when retained-memory profile justifies it. |
| **Goroutine leak** | Optimization spawns work without cancel/join/drain. | Define owner, context, channel close, and terminal wait. |
| **Pool state leak** | Reused object carries sensitive/stale state or escapes after Put. | Reset, define ownership, and never use after Put. |
| **Map order** | Candidate relies on iteration order. | Sort when contract requires order and benchmark that contract. |
| **Benchmark setup** | Input allocation/setup is timed inconsistently. | Place setup according to measured operation and document it. |

## Recovery discipline

Preserve the first observable Go optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Go optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
