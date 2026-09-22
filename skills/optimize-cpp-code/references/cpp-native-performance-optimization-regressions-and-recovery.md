# Optimization regressions and recovery for Cpp Native Performance

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
| **Dangling view** | `string_view`/span/reference outlives source. | Prove owner lifetime and test mutation/reallocation boundaries. |
| **Iterator invalidation** | Container change invalidates cached iterator/reference. | Use documented invalidation rules and boundary tests. |
| **Move semantics change** | Moved-from object or exception guarantee differs. | Preserve documented postconditions and strong/basic guarantee. |
| **Benchmark elision** | Compiler removes or constant-folds work. | Use harness consumers/black-box and inspect generated code. |
| **Allocator/ABI drift** | Candidate changes allocator, layout, exceptions, RTTI or target flags. | Match environment or classify as a separate tradeoff. |

## Recovery discipline

Preserve the first observable C++ optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the C++ optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
