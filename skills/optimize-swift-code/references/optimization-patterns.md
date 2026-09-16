# Evidence-driven Swift optimization patterns

Apply patterns only after the profile supports their cost center.

- reduce algorithmic work, copies and ARC traffic shown by Instruments.
- use borrowing/views/withUnsafe* only with scoped lifetime and no escape.
- preallocate/batch only for bounded representative sizes.
- specialize/existential removal only with profile and code-size/API tradeoff.
- concurrency only with actor/cancellation/order/backpressure preserved.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
