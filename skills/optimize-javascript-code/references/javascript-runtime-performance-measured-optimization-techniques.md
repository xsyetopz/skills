# Measured optimization techniques for Javascript Runtime Performance

Apply patterns only after the profile supports their cost center.

- remove repeated parsing, serialization, DOM work and allocations shown by
  profile.
- batch DOM/network/I/O while preserving responsiveness/backpressure.
- choose Map/Object/Array/typed arrays based on access and semantics.
- avoid deopt/object-shape churn only when runtime profile confirms.
- stream or chunk data only with cancellation/error/ordering contract.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
