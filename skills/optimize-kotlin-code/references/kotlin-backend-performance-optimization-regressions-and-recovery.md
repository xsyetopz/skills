# Optimization regressions and recovery for Kotlin Backend Performance

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
| **Sequence regression** | Small pipeline gets slower or changes exception timing/laziness. | Benchmark representative sizes and test side-effect/order semantics. |
| **Coroutine leak** | `GlobalScope`/unowned jobs outlive component. | Use structured scope and explicit cancellation/join. |
| **Cancellation swallowed** | Broad catch converts cancellation to success. | Rethrow/preserve cancellation according to API. |
| **Boxing surprise** | Value class/generic/interface path still boxes. | Inspect bytecode/profile for target backend. |
| **Backend conflation** | JVM evidence claimed for Native/JS. | Test and document selected backend only. |

## Recovery discipline

Preserve the first observable Kotlin optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Kotlin optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
