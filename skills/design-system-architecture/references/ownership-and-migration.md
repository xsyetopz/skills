# Assign software state ownership and migrate interfaces

In this software-architecture reference, a port is an application-facing
interface for a capability, not a TCP or UDP network endpoint. An adapter
implements that interface using a particular dependency. A platform port, when
discussed elsewhere, means adapting software to a different platform.

Procedures and examples, not a requirement to introduce adapters or services.

## Decide the boundary that changes behavior

For each relevant state value, identify its authoritative writer, readers,
lifetime, persistence and transaction scope. Then identify control authority:
who starts work, retries it, cancels it, orders it and reports failure. A cache
can own eviction without owning the underlying fact. A UI projection must not
become a second writable source of truth accidentally.

Example: a document editor has persisted text, an in-memory document model and a
search index. The document store owns committed text; the editing session owns
unsaved changes; the index owns a versioned projection. Search results include
document version. Opening a result re-resolves against current text rather than
trusting stale offsets. Keep indexing work outside the save transaction unless
consistency requires it.

Extract a boundary only where dependencies, lifetime or failure behavior need to
differ. A direct function call is appropriate for two modules sharing a process
and stable data contract. A port is useful when a consumer needs to select among
storage/tool implementations. A network service adds independent deployment and
partial failure; it is not a free substitute for a module.

## Contract shape and dependency direction

Example application-owned port:

```ts
type SaveResult =
  | { kind: "saved"; version: number }
  | { kind: "conflict"; currentVersion: number }
  | { kind: "unavailable"; retryable: boolean }
  | { kind: "unknown"; requestId: string };
interface DocumentStore {
  save(
    id: string,
    expectedVersion: number,
    text: string,
    requestId: string,
    signal: AbortSignal,
  ): Promise<SaveResult>;
}
```

The adapter translates database/HTTP errors into this contract; the application
decides how conflicts appear to the user. Specify whether cancellation means
“request stopped waiting” or “commit guaranteed not to happen.” Use
`unavailable` only when no commit occurred. Return `unknown` after transport
loss when commit status cannot be established. Reconcile by request ID before
retrying. The interface belongs near the consumer's semantics, while concrete
database types stay in the adapter.

Do not abstract every class or force all adapters into one
lowest-common-denominator API. Define units, encodings, ordering, nullability,
errors and version compatibility where components actually exchange data. JSON
Schema can describe structural validation but cannot prove transaction or
delivery semantics. [JSON Schema 2020-12][ref-json-schema-2020-12].

## Failure and idempotency

For a retryable write, define an idempotency key scoped to caller/operation,
store the key and result atomically with the effect, and reject reuse with
incompatible parameters. A timeout then permits querying/retrying the same
logical operation rather than creating another effect. Define retention:
expiring deduplication records too soon can allow a delayed retry to duplicate
work. Retry only transient failures with bounded backoff and an overall
deadline; do not retry invalid input or conflicts blindly. [AWS idempotent API
design][source-3].

For a database change plus emitted event, a transactional outbox stores the
event in the same transaction, and a publisher later delivers it. Delivery can
repeat; consumers must deduplicate or make effects idempotent. Define delivery
and business-effect guarantees separately. If no cross-process transaction is
needed, retain the simpler local transaction. [Transactional outbox][source-2].

## Generated artifacts and provenance

Record canonical input, generator/tool version, flags, output paths and
publishing owner. For OpenAPI-derived clients, change the source schema, run the
existing pinned generator and review public client diffs. Generated output may
be checked in for consumers; that alone is not competing authority. A manually
edited generated model that disagrees with its schema is competing authority.
Preserve upstream/license attribution for vendored artifacts.

Verify deterministic output in the repository's established generator workflow.
Nondeterministic timestamps, environment paths and unordered output can obscure
meaningful changes; repair only if required by the authorized generator work.
Avoid creating a new global scanner simply to validate one migration.

## Worked migration and rollback

To move storage access out of UI components:

1. Inventory callers, transactions, errors and persisted data. Define the
   application-owned contract from observed behavior.
1. Implement the adapter using the existing storage, preserving version/conflict
   semantics.
1. Move one complete user operation through the contract, including cancellation
   and tests. Keep UI objects out of the adapter.
1. Migrate remaining authorized consumers, then remove the obsolete direct path
   when no supported consumers remain.
1. Verify dependency direction and the representative read/write/conflict
   operation with the repository’s existing validation checks.

For rolling deployments, use expand/contract only if compatibility requires it:
add the new representation, deploy readers that understand both, backfill with
checkpointed progress, switch writers, verify, then retire the old
representation after the support window. Dual writes need an
authority/reconciliation rule; two successful calls are not atomic. Rollback
becomes constrained once new-only data exists, so define that point before
deployment. For immediate replacement, remove the old path after migrating its
consumers.

Use Michael Nygard’s ADR format for consequential decisions: title, status,
context, decision, and consequences. Record considered alternatives under
context. Mark superseded decisions and link their replacements. Retain the
original decision history. [ADR technique][source-1].

[source-1]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
[source-2]: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
[source-3]: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/

[ref-json-schema-2020-12]: https://json-schema.org/draft/2020-12
