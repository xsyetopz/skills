# Patterns and pipelines

Choose a mechanism only after naming the boundary it protects. Existing language
features—functions, ADTs, traits/protocols, modules, closures, channels, and
standard collections—often implement the pattern with less ceremony.

## Pattern families

- **Creation:** use a factory or constructor injection for runtime-selected or
  external construction. Call a constructor directly for one known type.
- **Structure:** use an adapter/anti-corruption layer for a real foreign
  contract, or a decorator for composable behavior. Avoid wrapper chains that
  only rename methods.
- **Behavior:** use a strategy/callback for current algorithm variation or a
  state machine for legal transitions. An enum and direct branch is simpler for
  a small stable choice.
- **Concurrency:** use a bounded queue, worker, actor, channel, or structured
  concurrency for measured coordination. Avoid unbounded queues and
  fire-and-forget tasks; use a direct call otherwise.
- **Resilience:** use timeout, bulkhead, circuit breaker, or retry with
  idempotency for an identified transient failure. Do not retry invalid input,
  conflicts, or unknown writes.
- **Persistence:** use a repository/data mapper when application and storage
  contracts differ. Do not place a generic repository over one ORM/query API.
- **Integration:** use request/reply, event, saga, or outbox for independent
  systems. A direct call is simpler for one same-process action.
- **Distributed coordination:** use leases or consensus only for quantified
  shared coordination. Prefer one authoritative writer or database constraint.

A pattern does not provide delivery, transaction, or security guarantees. Write
that guarantee explicitly and test it at the authoritative boundary.

## Pipelines have distinct operational contracts

- **In-process transform:** typed input/output and local errors; check stage
  output and failure propagation.
- **Compiler:** source/IR invariants and diagnostics; use fixtures across parse,
  lower, optimize, and codegen.
- **ETL:** provenance, schema evolution, replay, and batch atomicity; test
  checkpoints, rerun, and bad records.
- **Stream processing:** event time, ordering, watermarks, and backpressure;
  test late/duplicate events and recovery.
- **Message processing:** durability, acknowledgement, retry, and idempotency;
  test duplicate delivery and crash between effect/acknowledgement.
- **CI/CD:** artifact provenance, promotion, and rollback; check immutable
  artifacts and a rollback drill.

## Unnecessary queue

**Deciding condition:** The caller needs the save result synchronously in the
same process and transaction, with no recovery or scheduling requirement.

```ts
// RED: no durable status, capacity bound, retry policy, or idempotency key.
queue.push(() => saveInvoice(invoice));
```

Why it fails:

- the queue has no capacity, delivery, retry, or recovery contract;
- asynchronous execution loses the caller's direct result and transaction
  boundary without a stated requirement.

## Direct call until durable work is required

```ts
await saveInvoice(invoice);
```

Why it works:

- the caller needs the result now and shares the transaction boundary;
- a direct call introduces no new delivery or ordering state.

Check:

- if recovery or scheduling requires a queue, define bounded capacity,
  delivery, idempotency, status, and crash recovery, then test a full queue and
  a crash/retry path.

Sources: [Enterprise Integration
Patterns](https://www.enterpriseintegrationpatterns.com/),
[Azure architecture styles][azure-styles],
[AWS retries and idempotency][aws-idempotency].

[azure-styles]: https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/
[aws-idempotency]: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
