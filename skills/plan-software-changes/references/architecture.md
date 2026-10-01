# Architecture decisions

Read when a boundary, ownership, or contract is being chosen. Decide from
measured scenarios and the existing system, not from a pattern catalog.

## Quality scenario

"Make it scalable" is not a requirement. Write each quality claim as a
scenario: source, stimulus, environment, response, response measure
Clements, Kazman, Software Architecture in Practice). Drop any adjective that
has no measure; if the measure is unknown, it is an open decision and you
ask. Every scenario names the test or measurement that checks it.

## Decision record

Record: context, decision, rejected alternatives with the reason each lost,
consequences, and what would make you revisit. Write the rejected options
from the actual constraints (team size, deploy frequency, traffic), not from
general reputation. Keep it to one page.

## Module, port, or service

- Default to a module inside the existing deployable.
- Add a port (interface) when two implementations exist now; a test double
  counts. One implementation plus "we might swap the database" is a
  hypothetical need; do not add it.
- Add a service only for an independent deployment, scaling, or failure
  domain that the scenarios require. A service adds a network hop, partial
  failure, and a versioned contract; five engineers deploying daily with a
  small traffic share gain nothing from it.
- Add a queue only when a direct call fails a named requirement (burst
  absorption, decoupled availability, fan-out). Otherwise call directly.
- Add a factory, strategy, or repository only for a named boundary that has
  a second caller or implementation today.

## Source of truth

Map each piece of state to exactly one writer. Caches, search indexes, and
read models are projections and never write back. Two components claiming the
same state is a stop-and-ask: someone with authority decides first.

## Dependency direction

Domain code does not import adapters (storage, HTTP, SDKs). Put the rule where
CI runs it: a test that scans imports, or the repository's existing lint
configuration, and show it failing on a planted violation. An architecture
rule that is not checked erodes.

## Adapters and contracts

Write one contract test suite for the port and run every adapter through it,
including the in-memory one. Each adapter owns its resource's concurrency
(connections, threads); callers do not share a connection across threads.

## Invariants in the database

Uniqueness, foreign keys, required fields, and shape rules are `UNIQUE`,
`FOREIGN KEY`, `NOT NULL`, `CHECK`. A check only in application code loses to
a concurrent writer; the application catches the violation and reports a
domain error.

## Operation identity for retries

A retryable write carries an identity (for example an `Idempotency-Key`) that
the store enforces with a unique constraint, and the retry returns the
original result. Retry only transient failures; invalid input is never
retried. A retry of the whole handler after a partly successful write repeats
the write.

## HTTP errors

Return one tested error shape across endpoints; RFC 9457 problem details
(`type`, `title`, `status`, `detail`) is the standard one. Test it.

## Changing a contract two sides depend on

When producer and consumers deploy separately (API field, event, column,
config key), use parallel change: expand (producer emits old and new, same
value), migrate (each consumer switches and deploys), contract (remove the old
form). Removal waits for evidence that every consumer reads the new form
(confirmation, versions, or observed reads), not for a date. A single-deploy
rename of a shared contract breaks whichever side deploys second.

## Protocol and pipeline notes

- LSP framing `Content-Length` counts bytes, not characters. Positions are
  UTF-16 code units unless the client negotiates another encoding
  (`positionEncoding`); emoji break character-count positions.
- A cancelled request is not a rollback; work already done stays done.
- Pipelines (ETL, stream, CI) define for each stage its input contract,
  whether it is safe to rerun, and what happens to a failed record.
