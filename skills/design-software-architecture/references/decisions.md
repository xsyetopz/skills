# Architecture decisions

Deciding from measurable quality requirements, alternatives, and the
boundary a mechanism protects. The worked boundary decision is in
[`assets/boundary-decision-example.md`][example].

## Contents

- Quality attribute scenario
- Decision record with alternatives
- Module, port, or service
- Direct call before a queue
- Pattern only for a named boundary
- UI state with its owner

## Quality attribute scenario

**Definition.** A testable quality requirement: a stimulus, the
environment, the response, and a response measure (SEI Quality Attribute
Workshop, [QAW][qaw]). For example: "a retried order submission during a
network timeout creates exactly one order."

**Use when.** A decision depends on a quality: availability, latency,
evolvability, security, or cost.

**Do not use when.** You would write an adjective such as "scalable" or
"robust". It gives no test; write the scenario instead.

**Example.** From the orders example:

```text
Stimulus: client retries POST /orders after a timeout, same Idempotency-Key.
Environment: normal operation, SQLite store.
Response: the service returns the first order; no second row.
Measure: rows with that key == 1 (test_create_retry_and_read).
```

**Cost removed.** Debate over unmeasurable goals: each scenario becomes a
test that passes or fails.

**Verify.**

1. Every quality named in the decision has a scenario with a measure,
   and a test or measurement that checks it.

## Decision record with alternatives

**Definition.** A short record of one decision: context, decision, the
alternatives considered with the reason each was rejected, and the
consequences ([ADR][adr]). Record only decisions that were made.

**Use when.** Later readers will question a boundary, technology, or
protocol choice.

**Do not use when.** The choice is local and reversible, such as a
helper's name.

**Example.**

```markdown
# Store orders behind an OrderStore port

Context: tests need a fast store; production uses SQLite; one process.
Decision: define OrderStore (get, get_by_key, add) owned by the service.
Alternatives: call sqlite3 from the service (rejected: tests need a DB);
separate storage service (rejected: no independent deployment need).
Consequences: every adapter must pass the StoreContract tests.
```

**Cost removed.** Reversing decisions whose reasons were lost.

**Verify.**

1. Each rejected alternative has a stated reason that points to a
   scenario or a constraint.

## Module, port, or service

**Definition.**

- **Module:** a direct call in one process, sharing one data contract.
- **Port:** an interface the application owns, with more than one
  implementation today.
- **Network service:** adds independent deployment and partial failure,
  and costs operations effort ([Microservice Premium][premium]).

**Use when.** Choosing how two parts of a system communicate.

**Do not use when.** The choice is a port with one implementation and no
test double, or a service with no independent deployment or scaling
need.

**Example.** The orders example has a port because it has two stores
today: memory for tests, SQLite for use. The domain is a plain module,
and there is no service boundary.

**Cost removed.** Partial-failure handling and deployment work with no
requirement behind them.

**Verify.**

1. Every port has two or more implementations, or a test double in use.
   Every service has a documented independent-deployment need.

## Direct call before a queue

**Definition.** A queue adds durability, retries, ordering questions,
and duplicate delivery. Use one only when the work must survive a
crash, outlive the request, or be throttled.

**Use when.** The work can finish after the caller leaves, and losing
it is not acceptable.

**Do not use when.** The caller waits for the result anyway; a queue then
only adds latency and failure modes.

**Example.** `place_order` is a direct call. A queue would need
idempotent consumers and acknowledgement after the effect; the
`Idempotency-Key` design already covers retries at the HTTP edge.

**Cost removed.** Duplicate delivery handling and lost acknowledgements
in code that never needed asynchrony.

**Verify.**

1. For every queue, name the crash scenario it survives and point to a
   test with a duplicate delivery.

## Pattern only for a named boundary

**Definition.** Use a design pattern only when you can name the
boundary it protects:

| Family | Use when | Simpler default |
| --- | --- | --- |
| Factory / injection | Type selected at run time | Direct constructor |
| Adapter | A real foreign contract | Call it directly |
| Strategy | Algorithm varies today | Enum and branch |
| State machine | Legal transitions matter | Flag |
| Retry | Transient failure with operation identity | Fail fast |
| Repository | App and storage contracts differ | Query API directly |

**Use when.** Reviewing a proposal that adds a pattern.

**Do not use when.** The reason is "we might need it later". See
`$write-readable-code` ("never is often better than right now").

**Example.** `SqliteStore` is an adapter: `sqlite3` is a foreign contract
(SQL, threads, connections), and the port hides it.

**Cost removed.** Indirection that every reader traces and nobody uses.

**Verify.**

1. Every pattern in the diff maps to a row, with its condition met
   today.

## UI state with its owner

**Definition.** UI state lives with its only owner. Lift it to the
nearest common owner only when a second consumer exists. MVVM, MVI,
Redux, and component state structure that ownership; they are not system
architectures.

**Use when.** Deciding where a UI value lives.

**Do not use when.** You would put a single dialog's open flag in a
global store.

**Example.**

```ts
// One owner: local state.
const [open, setOpen] = useState(false);
```

**Cost removed.** Global actions and subscriptions for local state, and
the rerenders they cause.

**Verify.**

1. Every global store entry has at least two consumers or a restoration
   requirement.

[example]: ../assets/boundary-decision-example.md
[qaw]: https://insights.sei.cmu.edu/library/quality-attribute-workshops-qaws-third-edition/
[adr]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
[premium]: https://martinfowler.com/bliki/MicroservicePremium.html
