---
name: design-enterprise-software
description: >-
  Design or review enterprise-grade, long-lived, multi-team software for
  extensibility, compatibility, operability, security, governance, scale,
  and evolution. Use when concrete enterprise quality attributes require
  architectural tradeoffs; not merely because software runs in production.
---

# Design Enterprise Software

Use this skill when requirements include long-lived ownership, multiple teams,
stable contracts, compatibility, migrations, SLOs, compliance, deployment
safety, customization, or materially constrained scale. A small production CLI
or one-team service does not activate it.

Start with concrete quality-attribute scenarios: stimulus, environment,
measurable response, owner, and priority. Quantify users, requests/messages per
second, data, writes, tenants, regions, deployments, and team boundaries when
they matter. Identify authoritative owners, trust boundaries, consumers,
compatibility window, and failure/recovery behavior. Compare the smallest
structure with a more distributed/extensible alternative, including operating,
migration, and cognitive costs.

**DO NOT add layers, interfaces, factories, services, DTOs, schemas, plugins,
or process because they look enterprise-grade.** Every added boundary needs a
named quality attribute and a verification method. Prefer standards, platform
facilities, organization services, and maintained ecosystem components before
custom infrastructure. [FizzBuzzEnterpriseEdition][fizzbuzz] is an anti-example
of abstraction quantity, not architecture guidance.

## RED — DO NOT: add enterprise theatre

**Deciding condition:** Multiple teams need a stable invoice API, but no extra
runtime implementation, plugin axis, or storage abstraction is required.

```text
InvoiceFactoryProvider -> InvoiceStrategyRegistry -> InvoiceFacade
  -> InvoiceServiceImpl -> InvoiceRepositoryImpl -> InvoiceDtoMapper
```

No owner, compatibility promise, SLO, rollout, telemetry, or failure contract
exists, so these layers solve no stated requirement.

Why RED:

- abstraction quantity replaces the missing operational and compatibility
  decisions;
- the layers add cognitive cost without a measurable quality attribute.

## GREEN — DO: make contracts follow the actual force

```text
invoice/
  api/          # supported request/response contract
  domain/       # calculation invariants
  persistence/  # only when this service owns durable state
  telemetry/    # separately deployed operational diagnostics
```

Define owner, additive/breaking compatibility policy, actual availability and
latency objectives, idempotency for retried writes, canary/error gate, and
state-safe rollback. Check an old consumer, retried write, failed dependency,
and rollback path.

Why GREEN:

- each boundary corresponds to a current contract, state owner, or deployment
  concern;
- operational requirements are measurable rather than implied by class names.

Check:

- exercise an old consumer, retried write, failed dependency, and rollback path.

Read [enterprise quality attributes](references/quality-attributes.md) for the
applicable gate and [governance and delivery](references/governance-delivery.md)
for multi-team ownership, release, and supply-chain decisions. Keep rules that
are not justified by the stated system out of the design. Report rejected
alternatives, residual risks, and measurable validation; do not scaffold a
reference architecture for a design-only request.

[fizzbuzz]:
  https://github.com/EnterpriseQualityCoding/FizzBuzzEnterpriseEdition
