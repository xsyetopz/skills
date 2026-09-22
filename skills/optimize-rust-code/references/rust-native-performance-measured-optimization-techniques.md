# Measured optimization techniques for Rust Native Performance

Apply patterns only after the profile supports their cost center.

- reduce algorithmic work, allocations and copies indicated by profile.
- borrow/view data only when owner lifetime and retention are correct.
- choose container/layout/SmallVec/arena/pool only with workload/lifetime
  evidence.
- specialize/generic/dynamic dispatch based on profile and code-size tradeoff.
- SIMD/unsafe only with safe API invariants, target dispatch and differential
  tests.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
