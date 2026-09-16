# Evidence-driven Go optimization patterns

Apply patterns only after the profile supports their cost center.

- reduce algorithmic work and allocations indicated by pprof/benchmem.
- preallocate only from bounded realistic size; avoid retained oversized backing
  arrays.
- reuse with `sync.Pool` only for temporary objects with no identity/state
  assumptions.
- batch I/O/encoding and avoid repeated conversion/copy.
- concurrency only when workload and scheduler/contended profiles justify it.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
