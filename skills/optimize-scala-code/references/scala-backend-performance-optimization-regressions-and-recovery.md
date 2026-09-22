# Optimization regressions and recovery for Scala Backend Performance

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
| **View/laziness** | Side effects, exceptions or repeated traversal change. | Test order/count/error and materialization boundaries. |
| **Future context** | Blocking or parallelism moves to wrong execution context. | Preserve scheduler/EC and cancellation/resource semantics. |
| **Boxing folklore** | Generic rewrite assumed allocation-free. | Inspect profile/bytecode for target Scala/JVM. |
| **Collection type** | Candidate changes ordering, duplicates or mutability. | Preserve collection contract. |
| **Backend transfer** | JVM benchmark claimed for JS/Native. | Measure selected backend only. |

## Recovery discipline

Preserve the first observable Scala optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Scala optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
