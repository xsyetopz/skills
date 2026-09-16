# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Algorithmic complexity dominates | Change algorithm/data structure and measure representative sizes. | Micro-optimizing loop syntax. |
| Profile shows allocation/retention cost | Remove unnecessary work/copies or redesign ownership with memory evidence. | Pooling everything. |
| Contention/scheduling dominates | Reduce shared state/critical section or redesign work partition with concurrency semantics. | Adding more threads/tasks. |
| I/O/external service dominates | Batch/cache/parallelize only under protocol, consistency, idempotency and resource constraints. | CPU microbenchmark as application proof. |
| Compiler/JIT appears to remove cost | Use observable result/black-box and inspect generated work. | Trusting a tiny timing number. |
| Candidate benefits only one target/data size | Gate/dispatch or limit claim and preserve supported fallback. | Universal replacement. |

## Unresolved decisions

A material product, compatibility, public-interface, deployment, or policy
choice remains user-owned when repository evidence does not settle it. Present
the concrete alternatives and consequences. Routine implementation details that
do not change an external contract remain the agent's responsibility.

## Avoiding false precision

Use project-defined thresholds, limits, versions, and acceptance criteria. When
none exists, report measurements or uncertainty; do not invent a timeout,
reviewer count, confidence score, supported version, performance target, or
error budget and then treat it as a requirement.
