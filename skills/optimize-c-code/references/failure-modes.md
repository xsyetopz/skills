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
| **Signed overflow** | A faster arithmetic rewrite invokes undefined behavior. | Use checked/range proof or unsigned/wider arithmetic while preserving API behavior. |
| **`restrict` misuse** | Pointers actually alias in a supported call. | Establish and document/enforce non-aliasing at every call boundary. |
| **Lifetime/`realloc`** | Cached pointer survives reallocation or owner destruction. | Recompute pointers and verify ownership/cleanup paths. |
| **Vector tail** | SIMD path skips remainder, alignment, or unsupported CPU. | Test all lengths/alignments and retain dispatch/fallback. |
| **Error/errno loss** | Optimization changes partial-write/error propagation. | Preserve exact return, errno, and cleanup contract. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
