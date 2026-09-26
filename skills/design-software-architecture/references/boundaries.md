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

- Source-of-truth map
- Ports and adapters
- Contract tests shared by adapters
- Dependency direction check
- Adapter owns its resource's concurrency
- Operation identity for retries
- HTTP contract with problem details
- Parallel change for two-sided contracts

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
