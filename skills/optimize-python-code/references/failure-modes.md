# Failure modes and recovery

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
| **Iterator exhaustion** | Candidate consumes iterable twice or changes lazy timing. | Test one-shot iterators and side effects. |
| **Falsy/default conflation** | `x or default` changes valid 0/empty/False values. | Use explicit sentinel/None contract. |
| **Exception swallowing** | Fast path returns default instead of required error. | Preserve exception type/context and cleanup. |
| **Benchmark import/setup** | Different setup or environment is timed. | Use pyperf metadata/process isolation and same work. |
| **C-extension/GIL assumption** | Threading change relies on release/GIL behavior not true for target build. | Inspect extension/runtime/free-threaded support. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
