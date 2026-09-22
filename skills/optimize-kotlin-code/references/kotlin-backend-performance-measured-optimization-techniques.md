# Measured optimization techniques for Kotlin Backend Performance

Apply patterns only after the profile supports their cost center.

- reduce allocations/boxing and repeated transformations shown by profile.
- use sequences only when lazy pipeline/workload benefits outweigh iterator
  overhead.
- inline/value classes/functions only with ABI/boxing/backend evidence.
- batch coroutine/I/O work while preserving structured
  cancellation/backpressure.
- select data structures and primitive arrays based on actual domain/access.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
