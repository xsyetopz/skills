# Measured optimization techniques for Python Interpreter Performance

Apply patterns only after the profile supports their cost center.

- choose better algorithm/built-in/data structure based on profile.
- reduce repeated parsing/conversion/allocation and unnecessary materialization.
- move loops to optimized built-ins/libraries only with equivalent domain/error
  behavior.
- stream/chunk data when memory profile and lifetime support it.
- cache only with bounded keys, invalidation, memory ownership and concurrency.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
