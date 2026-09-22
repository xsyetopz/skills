# Measured optimization techniques for Scala Backend Performance

Apply patterns only after the profile supports their cost center.

- choose collection/data structure based on operations and sizes.
- fuse transformations/views only when laziness/side effects/traversal are
  equivalent.
- remove boxing/tuple/intermediate allocations where profile shows cost.
- batch effects/I/O while preserving execution context, order, cancellation and
  errors.
- specialize hot paths only with API/code-size/maintenance tradeoff.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
