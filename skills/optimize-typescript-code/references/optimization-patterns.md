# Evidence-driven TypeScript optimization patterns

Apply patterns only after the profile supports their cost center.

- reduce pathological type instantiation/inference while preserving public
  types.
- use project references/incremental build only with correct dependency graph
  and cache invalidation.
- optimize emitted runtime using actual JavaScript profile, not type syntax
  folklore.
- avoid repeated serialization/allocation and event-loop blocking.
- split type/runtime changes so compile-time and runtime effects are measured
  separately.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
