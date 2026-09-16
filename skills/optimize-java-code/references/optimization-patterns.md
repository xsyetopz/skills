# Evidence-driven Java optimization patterns

Apply patterns only after the profile supports their cost center.

- profile representative steady-state and startup separately.
- reduce allocation/boxing and algorithmic work before JVM flag tuning.
- choose primitive/specialized representations only where API cost is justified.
- batch I/O and reduce contention using measured lock/block profiles.
- cache only with bounded size, lifecycle, invalidation and classloader
  awareness.

## Technique review

For every candidate, state the removed work, expected profile change, affected
contracts, tradeoffs, supported target conditions, and rollback. Check whether
the optimization moves cost to startup, another thread/process, memory, code
size, external service, or cleanup.

Prefer a simpler algorithm/data representation over a brittle micro-optimization
when both meet the objective. Retain a more complex fast path only when the gain
is material, the fallback/dispatch is correct, tests discriminate failure, and
the maintenance/operational cost is acceptable.
