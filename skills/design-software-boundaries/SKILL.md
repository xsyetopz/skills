---
name: design-software-boundaries
description: >-
  Choose or review software architecture and boundaries, including long-lived
  multi-team systems with compatibility, operability, governance, or scale
  constraints. Not for routine implementation with no structural decision.
---

# Design Software Boundaries

Answer the decision from evidence, not a pattern name. State the operation, data
ownership, runtime/deployment model, quality-attribute scenarios, team and
consumer boundaries, state/failure model, and expected evolution. Trace one
representative operation in an existing system before proposing a replacement.

Compare the smallest viable structure with only relevant alternatives. For each,
state the quality attribute improved, cost, assumptions, ecosystem support,
simpler alternative, overuse failure, and how to test, observe, and migrate it.
Prefer platform and framework facilities before custom infrastructure. A module,
direct call, native state mechanism, or sequential function chain is the default
until an independently deployed, versioned, concurrent, durable, or untrusted
boundary proves otherwise.

Do not add an interface, factory, service, repository, event, schema version, or
protocol for a hypothetical future. Add one only for a current alternate
implementation, extension axis, compatibility boundary, required isolation, or
platform contract. For long-lived or multi-team systems, quantify scale,
compatibility windows, SLOs, ownership, rollout, recovery, and governance rather
than substituting abstraction quantity for operational decisions.

Read only the needed reference:

- [Architecture choices](references/architecture-choices.md) for system styles,
  quality scenarios, and boundary selection.
- [UI, paradigms, and principles](references/ui-paradigms-principles.md) for
  presentation state, language fit, and design principles.
- [Patterns and pipelines](references/patterns-pipelines.md) for recurring
  mechanisms, integration, concurrency, and pipeline semantics.
- [Language layout](references/language-layout.md) for cohesive modules,
  visibility, import/runtime boundaries, and package validation.
- [Service contracts](references/service-contracts.md) for independently
  deployed contracts and observability.
- [Ownership and migration](references/ownership-and-migration.md) for writers,
  idempotency, rollback, and ADRs.
- [Quality attributes](references/quality-attributes.md) for measurable
  availability, latency, scale, compatibility, security, and recovery scenarios.
- [Governance and delivery](references/governance-delivery.md) for multi-team
  ownership, rollout, compliance, customization, and supply-chain decisions.

For implementation, migrate authorized consumers, retire obsolete paths, and
verify dependency direction plus representative normal and failure paths. For a
design-only request, report the decision, rejected alternatives, assumptions,
and validation plan without scaffolding.
