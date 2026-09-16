# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| One-function/local change with clear tests | Write a compact checklist or no persistent plan if not requested. | A multi-stage roadmap. |
| Cross-component protocol change | Plan both sides, compatibility/migration, integration evidence, and rollout order. | Server-only task. |
| Data format changes | Plan readers/writers, migration/backfill, validation, coexistence, rollback/recovery, and cleanup. | Schema edit plus unit test. |
| Unknown implementation feasibility | Add time-bounded experiment with explicit decision output. | Pretending uncertainty is solved. |
| Parallel tasks share files/contracts | Serialize or assign one owner; parallelize only disjoint work. | Concurrent conflicting edits. |

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
