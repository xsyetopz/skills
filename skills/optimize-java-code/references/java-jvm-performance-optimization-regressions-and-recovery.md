# Optimization regressions and recovery for Java JVM Performance

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
| **JMH dead code** | Result is unused or constant-folded. | Return/consume result and vary realistic inputs; inspect generated work. |
| **Warmup mismatch** | Candidate appears fast due to tiering/profile state. | Use forks/warmup and report startup separately. |
| **Stream rewrite** | Ordering, short-circuiting, exceptions or boxing changes. | Test semantic partitions and profile actual pipeline. |
| **Unsafe publication** | Lock removal exposes partially initialized/stale state. | Preserve JMM happens-before and concurrency tests. |
| **JVM flag tuning** | Benchmark uses flags not deployable or matched. | Record and match actual runtime/container limits. |

## Recovery discipline

Preserve the first observable Java/JVM optimization failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Java/JVM optimization appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
