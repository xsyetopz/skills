# Evidence-driven C optimization patterns

Apply patterns only after the profile supports their cost center.

- algorithm/data-structure changes before micro-tuning.
- contiguous data and structure-of-arrays only when access patterns justify it.
- batching syscalls/I/O and removing repeated parsing or allocation.
- restrict/vectorization/alignment only with proven alias and bounds contracts.
- arena/pool ownership only with bounded lifetime and cleanup.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
