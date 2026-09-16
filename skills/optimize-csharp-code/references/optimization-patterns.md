# Evidence-driven C# optimization patterns

Apply patterns only after the profile supports their cost center.

- remove repeated parsing/allocation and choose appropriate data
  representations.
- use spans/pooling only with lifetime/ownership measurements and cleanup.
- batch async/I/O while preserving cancellation, ordering, backpressure and
  exceptions.
- avoid boxing/interface/delegate/closure costs where the profile proves
  material.
- source generation/AOT/reflection changes only with deployment/trim
  compatibility.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
