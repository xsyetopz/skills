# Boundaries, ownership, and contracts

Drawing and enforcing boundaries. Every card uses the orders example in
[`assets/examples/orders/`][orders]:

- a domain module;
- an `OrderStore` port;
- memory, SQLite, and HTTP adapters;
- layer rules in `layers.json`.

`assets/examples/verify.sh` runs its tests, checks the layers, and
plants a violation.

## Contents

- [Source-of-truth map](#source-of-truth-map)
- [Ports and adapters](#ports-and-adapters)
- [Contract tests shared by adapters](#contract-tests-shared-by-adapters)
- [Dependency direction check](#dependency-direction-check)
- [Package cohesion: what goes in one package][toc-1]
- [Stable dependencies: which way packages depend][toc-2]
- [Adapter owns its resource's concurrency][toc-3]
- [Invariants enforced by database constraints][toc-4]
- [Operation identity for retries](#operation-identity-for-retries)
- [HTTP contract with problem details](#http-contract-with-problem-details)
- [Parallel change for two-sided contracts][toc-5]

[toc-1]: #package-cohesion-what-goes-in-one-package
[toc-2]: #stable-dependencies-which-way-packages-depend
[toc-3]: #adapter-owns-its-resources-concurrency
[toc-4]: #invariants-enforced-by-database-constraints
[toc-5]: #parallel-change-for-two-sided-contracts

## Source-of-truth map

**Definition.** For each piece of state, record:

- its one authoritative writer;
- its readers;
- its lifetime;
- its transaction scope.

A cache or projection owns only its copy, never the fact.

**Use when.** You are about to split a system, or two components both
"update" the same value.

**Do not use when.** State is local to one function.

**Example.**

| State | Writer | Readers | Lifetime |
| --- | --- | --- | --- |
| Order rows | `OrderStore.add` | service, HTTP GET | durable |
| Idempotency key → order | `OrderStore.add` (UNIQUE) | `place_order` | durable |
| DB connection | `SqliteStore` | its own methods | process |

**Cost removed.** Two writers of the same fact, causing lost updates and
conflicting truths.

**Verify.**

1. `rg -n 'INSERT|UPDATE|DELETE' src/` finds writes only in the listed
   writer.

## Ports and adapters

**Definition.** The application defines a port: an interface in its
own terms. Adapters implement the port for specific technologies. The
domain and the service depend on the port, never on an adapter
([Hexagonal Architecture][hex]).

**Use when.** A capability has two or more implementations today, or
needs a test double.

**Do not use when.** There is one implementation and no test needs a
double. See [module, port, or service][mps].

**Example.** From `orders/ports.py`:

```python
class OrderStore(Protocol):
    def get(self, order_id: str) -> Order | None: ...

    def get_by_key(self, idempotency_key: str) -> Order | None: ...

    def add(self, order: Order, idempotency_key: str) -> Order:
        """Store order; if the key exists, return the stored order instead."""
        ...
```

`orders/service.py` imports only the port type.

**Cost removed.** Business logic tied to one database. The service tests
run on `MemoryStore` in milliseconds.

**Verify.**

1. `check_layers.py` reports that no service or domain file imports an
   adapter.

## Contract tests shared by adapters

**Definition.** One test suite that states the port's contract, run
against every adapter.

**Use when.** A port has more than one adapter.

**Do not use when.** The test checks an adapter-specific detail, such as
SQL text; that belongs in the adapter's own tests.

**Example.** From `tests/test_orders.py`:

```python
ADAPTERS = {"memory": MemoryStore, "sqlite": SqliteStore}

def test_same_key_returns_first_order(self):
    for name, factory in ADAPTERS.items():
        with self.subTest(adapter=name):
            store = factory()
            first = store.add(new_order("o1", "ada", {"pen": 2}), "k1")
            second = store.add(new_order("o2", "ada", {"pen": 2}), "k1")
            self.assertEqual(second, first)
```

**Cost removed.** A fake that behaves differently from production, such
as a memory store passing tests that SQLite would fail.

**Verify.**

1. Adding a new adapter to `ADAPTERS` runs every contract test on it.

## Dependency direction check

**Definition.** The allowed import directions between layers, enforced
by `scripts/check_layers.py` from a rules file. It also reports files
in no layer and import cycles.

**Use when.** The architecture has layers or a dependency rule worth
keeping.

**Do not use when.** No rules are agreed yet. Agree on them first instead
of encoding the current accidents.

**Example.** Measured in `verify.sh` after planting
`from orders.adapters.sqlite import SqliteStore` in `domain.py`:

```text
orders/domain.py:30: domain imports adapters (orders/adapters/sqlite.py);
  allowed: []     (one line in the real output)
import cycle: orders/domain.py -> orders/adapters/sqlite.py -> orders/domain.py
```

**Cost removed.** Architecture eroding one import at a time, which review
catches late or never.

**Verify.**

1. `check_layers.py layers.json` reports `0 violation(s)` in CI.

## Package cohesion: what goes in one package

**Definition.** Robert C. Martin's three package cohesion principles
([Granularity][granularity]):

- REP, reuse/release equivalence: "THE GRANULE OF REUSE IS THE GRANULE
  OF RELEASE."
- CCP, common closure: "THE CLASSES IN A PACKAGE SHOULD BE CLOSED
  TOGETHER AGAINST THE SAME KINDS OF CHANGES. A CHANGE THAT AFFECTS A
  PACKAGE AFFECTS ALL THE CLASSES IN THAT PACKAGE."
- CRP, common reuse: "THE CLASSES IN A PACKAGE ARE REUSED TOGETHER. IF
  YOU REUSE ONE OF THE CLASSES IN A PACKAGE, YOU REUSE THEM ALL."

CCP pulls code that changes together into one package; CRP pushes apart
code that is not used together. They pull in opposite directions, so a
package boundary is a trade-off between them, not a rule to satisfy.

**Use when.**

- Deciding whether to split a package or merge two.
- `$find-code-smells` reports files in different packages that change
  together (CCP broken), or a package whose users each import a
  different part of it (CRP broken).

**Do not use when.**

- The package is not released or reused separately; REP then says
  nothing, and CCP alone decides.
- The history is too short to show what changes together.

**Example.** In the orders example, adding an order field would edit the
domain's `Order`, the port that stores it, and the service that builds
it with `new_order`, so the three share the `orders` package (CCP). The
SQLite and HTTP adapters are separate modules under `orders/adapters/`,
so a user of the memory adapter does not import `sqlite3` code it never
calls (CRP).

**Cost removed.** Releases forced by code a user does not use, and a
change that must edit several packages at once.

**Verify.**

1. For a proposed split, the change-coupling scan shows the new
   packages' files changing mostly with files in the same package.

## Stable dependencies: which way packages depend

**Definition.** Martin's package coupling principles
([Granularity][granularity], [Stability][stability]):

- ADP, acyclic dependencies: "THE DEPENDENCY STRUCTURE BETWEEN PACKAGES
  MUST BE A DIRECTED ACYCLIC GRAPH (DAG)."
- SDP, stable dependencies: "THE DEPENDENCIES BETWEEN PACKAGES IN A
  DESIGN SHOULD BE IN THE DIRECTION OF THE STABILITY OF THE PACKAGES."
- SAP, stable abstractions: "PACKAGES THAT ARE MAXIMALLY STABLE SHOULD
  BE MAXIMALLY ABSTRACT. INSTABLE PACKAGES SHOULD BE CONCRETE."

The metrics come from the same paper. Ca (afferent) is the number of
classes outside the package that depend on classes inside it. Ce
(efferent) is the number of classes inside that depend on classes
outside. Instability is I = Ce ÷ (Ca + Ce), from 0 (maximally stable)
to 1. Abstractness is A = abstract classes ÷ total classes, and the
distance from the main sequence is D = |A + I − 1| ÷ √2.

**Use when.**

- The dependency direction check reports a cycle (ADP).
- A package many others depend on keeps changing, and each change breaks
  its dependents (SDP).

**Do not use when.**

- The code has one package; the metrics need several to compare.
- A stable package is concrete on purpose, such as a value-type or
  standard-library package that is not expected to change. SAP's
  pressure to abstract does not apply to it.

**Example.** The orders layers, counting modules as the paper counts
classes, measured from the example's `from orders.` imports:

| Layer | Ca | Ce | I |
| --- | --- | --- | --- |
| `domain` | 5 | 0 | 0 |
| `ports` | 2 | 1 | 0.33 |
| `service` | 1 | 1 | 0.5 |
| `adapters` | 0 | 3 | 1 |

Every import goes from a higher I to a lower one, so SDP holds, and
`check_layers.py` reports no cycle, so ADP holds. `ports` holds the
abstract `OrderStore` and is more stable than the adapters that
implement it (SAP).

**Cost removed.** Changes to a volatile package that ripple into the
packages that should be stable, and cycles that force two packages to
be released together.

**Verify.**

1. `check_layers.py` reports no import cycle.
1. For each dependency between packages, I of the importer is higher
   than I of the imported package; list any exception with its reason.

## Adapter owns its resource's concurrency

**Definition.** An adapter that holds a resource (a connection, file, or
socket) also owns that resource's rules for threads, lifetime, and
closing, so callers need not know them.

**Use when.** The adapter is called from threads, tasks, or several
servers.

**Do not use when.** One caller uses the adapter on one thread.

**Example.** The HTTP adapter's threading server calls the SQLite
store from worker threads. `sqlite3` connections refuse this by default
([sqlite3][sqlite3]). The first test run failed with:

```text
sqlite3.ProgrammingError: SQLite objects created in a thread can only be
used in that same thread.
```

The fix belongs inside the adapter, because the adapter created the
connection: `check_same_thread=False`, one lock around every call, and a
`close()` method.

**Cost removed.** Thread errors and resource leaks that surface only
under a real server. The tests now pass under `python3 -W error`, which
turns unclosed connections into failures.

**Verify.**

1. The HTTP tests pass, and the suite runs clean under `-W error`.

## Invariants enforced by database constraints

**Definition.** Encode a data invariant — uniqueness, a foreign key, a
required field, or a shape or range rule — as a database constraint
(`UNIQUE`, `FOREIGN KEY`, `NOT NULL`, `CHECK`), so the database rejects a
violation for every writer, not only the one that runs the application's
check. Keep the application check too, but only to give a clear domain
error: catch the constraint violation and map it, rather than trusting
the check alone to keep the data valid.

**Use when.** More than one process, thread, or client can write the
same table: concurrent requests, a retry, an admin script, or another
service sharing the database.

**Do not use when.** The data lives only in one process's memory for its
lifetime, with no other writer to race.

**Example.** `orders/adapters/sqlite.py` declares the invariants in the
schema, not only in code:

```sql
CREATE TABLE orders (
  order_id TEXT PRIMARY KEY, customer TEXT NOT NULL,
  items TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE)
```

`new_order` rejects a missing customer or a non-positive count first, for
a readable message, but it is the `UNIQUE` column that actually stops two
racing writers from creating two orders for one key:
`test_same_key_returns_first_order` calls `store.add` twice directly,
bypassing the service's own duplicate handling, and still gets one order.

**Cost removed.** A second writer, a bulk script, or a code path that
skips the application check leaving duplicate, orphaned, or missing-field
rows that no test on the application layer ever saw.

**Verify.**

1. A write that skips the application check (a raw `INSERT`, another
   client, a second thread) still fails, or converges, at the store.

## Operation identity for retries

**Definition.** Give a retryable write an identity, such as an
`Idempotency-Key` header ([IETF draft][idem]), and enforce it at the
authoritative store with a UNIQUE constraint. A retry with the same key
returns the first result.

**Use when.** A client may retry after a timeout: payments, orders,
messages.

**Do not use when.** The request failed on invalid input or a conflict; a
retry fails again.

**Example.** `place_order` looks the key up, and `SqliteStore.add` uses
`INSERT OR IGNORE` on a UNIQUE key column, so concurrent retries also
converge.

**Cost removed.** Duplicate orders on retry.
`test_without_identity_a_retry_duplicates` shows the failure mode, and
`test_retry_with_same_key_creates_one_order` shows the fix.

**Verify.**

1. The HTTP retry test returns the same `order_id` for the same key.

## HTTP contract with problem details

**Definition.** Status codes, media types, and error bodies are part of
the API. Errors use `application/problem+json` with `type`, `title`,
`status`, and `detail` ([RFC 9457][rfc9457]).

**Use when.** Exposing any HTTP API.

**Do not use when.** The project has an established error format. Keep
it; do not introduce a second one.

**Example.** A missing `Idempotency-Key` returns 400, a domain rule
violation returns 422 with `detail`, and an unknown order returns 404.
`test_errors_are_problem_details` asserts all three, including the
content type.

**Cost removed.** Clients parsing ad-hoc error strings.

**Verify.**

1. Each error path has a test that asserts the status, the content
   type, and the `detail`.

## Parallel change for two-sided contracts

**Definition.** Change an interface between producer and consumer in
three steps:

1. **expand:** support both the old and the new form;
1. **migrate:** move every consumer to the new form;
1. **contract:** remove the old form.

Each step ships on its own ([Parallel Change][parallel]).

**Use when.** The producer and consumer deploy separately: APIs,
events, database columns, or LSP servers and clients.

**Do not use when.** Both sides live in one repository and can change in
one commit; change them together.

**Example.** To rename JSON `quantity` to `item_count`:

1. The server emits both fields.
1. Clients read `item_count`.
1. Once logs show no client reading `quantity`, the server drops it.

**Cost removed.** Breaking consumers during a deploy window.

**Verify.**

1. Between steps, a contract test for each consumer version passes
   against the deployed producer.

[orders]: ../assets/examples/orders/
[hex]: https://alistair.cockburn.us/hexagonal-architecture/
[mps]: decisions.md#module-port-or-service
[sqlite3]: https://docs.python.org/3/library/sqlite3.html
[idem]: https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/
[rfc9457]: https://www.rfc-editor.org/rfc/rfc9457
[parallel]: https://martinfowler.com/bliki/ParallelChange.html
[granularity]: http://web.archive.org/web/2011id_/http://www.objectmentor.com/resources/articles/granularity.pdf
[stability]: http://web.archive.org/web/2011id_/http://www.objectmentor.com/resources/articles/stability.pdf
