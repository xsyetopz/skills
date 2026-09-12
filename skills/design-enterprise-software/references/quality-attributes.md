# Enterprise quality attributes

Apply only the gates justified by the product. Write each requirement as a
scenario, for example: “During a regional dependency outage, finalize requests
return a known outcome or an idempotent reconciliation reference within 5
seconds.” Do not call a design scalable, secure, or extensible without a measure
and a boundary.

## Evolvability, compatibility, and customization

Name the owning team and supported consumers for every public API, event,
schema, and extension point. Define additive versus breaking changes, unknown
field/enum behavior, support window, deprecation owner, and removal criterion.
Test old and new consumers before rollout. Use expand/contract only when
independently deployed consumers require it; define the point after which
rollback cannot restore new-only data.

Choose one extension mechanism for one real variation: configuration for policy
or data, callback/strategy for local algorithm selection, plugin API for
independently delivered code, protocol boundary for an independent process, and
scripting only under a safe execution model. Each requires ownership,
versioning, isolation, and removal policy. A plugin mechanism is not a
substitute for a configurable value.

## Reliability and operability

Identify dependency, capacity, malformed-input, partial-commit, deployment, and
operator failure modes. Retry only transient operations with bounded backoff,
deadline, and idempotency/reconciliation; never retry validation failures or
unknown writes blindly. Define recovery, data-loss policy, and failure
isolation.

Set service-level indicators, objectives, and alerting based on user-important
outcomes. Error budgets guide release decisions only when an actual objective
and measurement exist. Instrument actionable state using the existing logs,
metrics, traces, and deployment tooling. Bound queues, cardinality, retention,
and telemetry cost; a telemetry outage must not change business commit behavior.
Create runbooks and exercise incident/rollback paths when humans operate them.

### RED — DO NOT: retry without an effect identity

**Deciding condition:** A write can commit before its response is lost, and the
caller may retry after a timeout.

```ts
// RED: a timeout can mean the invoice committed but the response was lost.
for (let attempt = 0; attempt < 3; attempt++) await createInvoice(input);
```

Why RED:

- a timeout can mean the invoice committed but its response was lost;
- retrying an unidentified effect can create duplicate invoices.

### GREEN — DO: retry an identified logical operation

```ts
await createInvoice({ ...input, idempotencyKey });
```

Why GREEN:

- the authoritative writer records the key and result atomically with the
  effect;
- incompatible key reuse is rejected and retention is explicit.

Check:

- test timeout-after-commit, duplicate delivery, incompatible key reuse, and
  expired-key behavior.

## Security, privacy, and supply chain

Document trust boundaries and data classification. Apply least privilege and
separate authorization from propagated trace context. Define audit evidence,
retention, residency, and access controls only where obligations require them.
Use maintained dependencies and organization/platform controls first. When risk
or policy requires it, make provenance, signing, SBOMs, vulnerability response,
and reproducible builds verifiable rather than decorative checkboxes.

## Scale, cost, and maintainability

Quantify the limiting dimension—requests, messages, data, write rate, fan-out,
tenants, regions, deployment count, or team count—and measure the bottleneck.
Remove it in the single authoritative system before distributing work unless
availability, isolation, or scale proves distribution necessary. Define tenant
isolation and noisy-neighbor behavior where multi-tenancy exists. Make capacity
and cost visible to owners.

Reduce dominant change cost: cohesive modules, controlled dependencies,
discoverable concepts, and standards replace bespoke infrastructure. Record
consequential decisions and trade-offs, not every class. Architecture must make
local reasoning easier; a new platform, service, or abstraction that only adds
cognitive overhead fails this gate.

Sources: [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html),
[Google SRE SLOs](https://sre.google/workbook/implementing-slos/),
[OpenTelemetry sensitive
data](https://opentelemetry.io/docs/security/handling-sensitive-data/),
[OpenSSF Supply-chain Levels for
Software Artifacts](https://slsa.dev/spec/v1.0/).
