# Measured optimization techniques for Cpp Native Performance

Apply patterns only after the profile supports their cost center.

- algorithm and data-layout changes before syntax churn.
- avoid repeated allocation/copy with views/ownership proven.
- reserve/batch only when growth and memory tradeoffs match workload.
- specialize or remove dynamic dispatch only where profile shows cost.
- SIMD/parallelism only with target dispatch, tails, exceptions and ordering
  defined.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
