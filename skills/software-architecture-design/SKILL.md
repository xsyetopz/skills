---
name: software-architecture-design
description:
  Design or review module ownership, dependency direction, public contracts,
  generated-code ownership, and structural migrations. Excludes routine edits
  that preserve existing boundaries.
---

# Software Architecture Design

Trace the relevant code, consumers, state, and constraints. Identify the
boundary requiring different ownership, dependencies, lifecycle, transactions,
deployment, failure handling, or compatibility.

Choose the smallest structure that resolves the demonstrated problem. Define
authoritative writers, control of retries/cancellation, public inputs/outputs,
and failure semantics. Use native protocol/schema contracts where available. Do
not add layers, interfaces, naming rules, or file quotas without a concrete
need.

Read [ownership and migration][ref-1] for contracts, idempotency, generated
provenance, migration, rollback, and Nygard-style ADRs.

For implementation, migrate affected consumers and retire obsolete paths. Verify
dependency direction, representative state transitions, and changed generator
output with relevant project checks. Report the resulting ownership decision and
material unresolved risks.

[ref-1]: references/ownership-and-migration.md
