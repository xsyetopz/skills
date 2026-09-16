# Phase 2: design the software implementation

Goal: freeze **how the system will satisfy the requirements** before production
implementation begins.

## Required design content

Address, as applicable:

- architecture and subsystem boundaries;
- public and internal interfaces;
- data representation and invariants;
- ownership/lifetime/concurrency model;
- error and cancellation semantics;
- persistence and migration behavior;
- dependency graph and allowed dependency direction;
- build/package topology;
- security boundaries and trust assumptions;
- performance-critical paths and measurement plan;
- observability/diagnostics;
- compatibility mapping from old to new system;
- implementation work breakdown and file/module ownership;
- integration order and verification environments.

For a mechanical software translation, provide explicit source-to-target
mappings for language constructs, ownership, error handling, FFI, async
behavior, platform APIs, and unsafe code. Prefer a table over asking each
implementer to rediscover rules.

## Feasibility probes

Use small throwaway or isolated probes when a design assumption cannot be
resolved from documentation/source inspection. A probe must state:

1. hypothesis;
1. minimal experiment;
1. observed result;
1. design decision affected;
1. whether probe code is discarded or intentionally retained.

Do not let probes become undeclared production implementation.

## Independent software design review

Use one proportionate independent review pass when needed. Give the reviewer
requirements and the design candidate. Additional specialist review must have a
distinct evidenced need or an explicit project requirement, not a fixed quota.
Inspect the relevant risks:

- requirement contradictions or omissions;
- interface/lifetime/concurrency failures;
- integration/dependency cycles;
- untestable requirements;
- platform/compatibility gaps;
- designs that require later workers to guess.

## Phase completion check

Advance only when every requirement is allocated to design elements, interfaces
are defined at ownership boundaries, integration order is feasible, verification
has a concrete plan, and all blocking review findings are resolved.

Freeze both the design and the implementation work breakdown.
