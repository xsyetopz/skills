# Optimization regressions and recovery for Rust Native Performance

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
| **Clone removal** | Borrow keeps huge owner alive or changes API lifetime. | Measure retained memory and prove owner lifetime. |
| **Iterator semantics** | Eager/lazy rewrite changes side effects/errors/order. | Test one-shot and error paths. |
| **Unsafe fast path** | Validity/provenance/alignment/tail invariant is only commented. | Enforce safe boundary and run differential/Miri/sanitizer where supported. |
| **Async cancellation** | Optimization moves resource cleanup past cancellation/drop. | Test cancellation at await points and drop behavior. |
| **CPU target** | Native features produce artifact incompatible with supported fleet. | Use dispatch/fallback or approved deployment target. |

## Recovery discipline

Preserve the first observable Rust optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Rust optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
