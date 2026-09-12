# Governance and delivery

## Ownership and governance

Map product and platform responsibilities: name the team owning each capability
and runtime, API/schema, data, on-call response, and deprecation decision. Match
boundaries to communication and ownership where feasible; Conway's Law is a
design force, not a mandate to reorganize teams. Use platform services when they
provide a supported common capability; do not force every team onto a platform
for a local need.

Govern APIs and data at their actual compatibility boundaries: named owner,
review/change process proportionate to blast radius, contract tests, and
migration window. Use ADRs for consequential choices with context, decision,
consequences, alternatives, and supersession link. Architecture review should
surface risks and trade-offs; it must not become a diagram approval ritual.
Policy-as-code is appropriate when policy is repeatedly evaluated and auditable;
a static, infrequently changed rule may belong in normal configuration/code.

## Release and change safety

Build once from pinned inputs, retain the artifact identity, and promote that
same artifact. Select feature flags, canaries, progressive delivery, or a direct
release based on blast radius and observability. A flag needs an owner, default,
expiry/removal condition, and safe interaction behavior. A canary needs a metric
and error threshold that can stop promotion. Define rollback before deployment:
code rollback can be unsafe after an irreversible data migration.

For a migration, identify data authority, compatibility readers/writers,
checkpointing, verification, and the state at which rollback is constrained.
Exercise recovery and restore where loss is unacceptable. Do not require a
multi-stage release for an atomically deployed private change.

## Review checklist

- Owner, consumers, trust boundary, and data authority are named.
- Compatibility promise, versioning mechanism, and deprecation/removal policy
  exist only for independently evolving consumers.
- SLO/SLI, alert action, incident owner, and failure isolation are defined when
  availability is required.
- Deployment, rollback, migration, and release evidence match blast radius.
- Scale, tenancy, residency, retention, and cost are quantified when applicable.
- Supply-chain and audit controls match threat model or policy.
- The design uses the least complex standard/platform/ecosystem mechanism that
  satisfies the scenario.

Sources: [Conway's Law](https://www.melconway.com/Home/Committees_Paper.html),
[Google SRE error budgets](https://sre.google/workbook/error-budget-policy/),
[NIST Secure Software Development
Framework](https://csrc.nist.gov/pubs/sp/800/218/final),
[OpenAPI Specification](https://spec.openapis.org/oas/latest.html),
[Architecture decision records][adr].

[adr]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
