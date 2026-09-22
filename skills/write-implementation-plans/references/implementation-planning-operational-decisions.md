# Operational decisions for Implementation Planning

Use this guide after inspecting the request and target system for implementation
plan. It selects an evidence path; it does not grant permission for an external
write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| One-function/local change with clear tests | Write a compact checklist or no persistent plan if not requested. | A multi-stage roadmap. |
| Cross-component protocol change | Plan both sides, compatibility/migration, integration evidence, and rollout order. | Server-only task. |
| Data format changes | Plan readers/writers, migration/backfill, validation, coexistence, rollback/recovery, and cleanup. | Schema edit plus unit test. |
| Unknown implementation feasibility | Add time-bounded experiment with explicit decision output. | Pretending uncertainty is solved. |
| Parallel tasks share files/contracts | Serialize or assign one owner; parallelize only disjoint work. | Concurrent conflicting edits. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
implementation plan remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
implementation plan. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
