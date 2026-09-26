---
name: design-software-architecture
description: >-
  Designs and reviews system boundaries: modules, ports, or services, state
  ownership, dependency rules, idempotent operations, and API and protocol
  contracts. Use for architecture decisions, service splits, or layering
  problems. Not for requirement wording.
---

# Design Software Architecture

Decide boundaries from measurable quality scenarios and the existing
system, then enforce them with tests and checks. The worked example is
`assets/examples/orders/`: a domain module, an `OrderStore` port, and
memory, SQLite, and HTTP adapters. `assets/examples/verify.sh` runs the
contract tests for both stores, idempotent retries, RFC 9457 errors, the
layer rules plus a planted violation, and LSP framing.

## Workflow

1. Read what exists: modules, imports, data stores, deployment units,
   and who writes each piece of state ([source of truth][truth]).
1. Write the quality requirements as scenarios with measures
   ([scenarios][scenario]). Drop any adjective that has no measure.
1. For each proposed boundary, choose module, port, or service by the
   cards' conditions ([choice][mps]). Choose a queue or a pattern only
   for a named need ([queue][queue], [patterns][patterns]).
1. Record the decision, with the rejected alternatives ([record][adr]).
1. Enforce it:
   - layer rules with `scripts/check_layers.py` ([direction][direction]);
   - shared contract tests for the adapters ([contracts][contracts]);
   - identity on retryable writes ([idempotency][idem]);
   - a tested error format ([HTTP][http]).
1. Change contracts between separately deployed parts with parallel
   change ([expand/contract][parallel]).
1. Report the scenarios with their tests, the checker output, and the
   decisions that remain open.

## Route the question to a card

| Question | Card |
| --- | --- |
| "Make it scalable/robust" | [Quality scenario][scenario] |
| Record a choice | [Decision record][adr] |
| Microservice or module? | [Module, port, or service][mps] |
| Add a queue? | [Direct call before a queue][queue] |
| Add a factory/strategy/repository? | [Pattern for a named boundary][patterns] |
| Who owns this data? | [Source-of-truth map][truth] |
| Swap storage or mock it | [Ports and adapters][ports], [contract tests][contracts] |
| Keep layers clean | [Dependency direction][direction] |
| Thread or connection errors in an adapter | [Adapter owns concurrency][concurrency] |
| Duplicates on retry | [Operation identity][idem] |
| API error format | [Problem details][http] |
| Change an API or event shape | [Parallel change][parallel] |
| Editor language server or debugger | [LSP framing][lsp], [positions][positions], [lifecycle][lifecycle], [DAP][dap] |
| ETL, stream, queue, CI pipeline | [Pipeline contracts][pipelines] |
| One capability, several editors | [Host adapter][host] |
| Global vs local UI state | [UI state][ui] |

## Rules

- Every quality claim has a scenario with a measure, and a test or
  measurement.
- Add a port only when two implementations exist today (a test double
  counts). Add a service only for an independent deployment or scaling
  need.
- Each piece of state has one authoritative writer, and projections
  never write back.
- Dependency rules live in a checked file (`layers.json`) and run in
  CI. Architecture that is not checked erodes.
- Every adapter passes the same port contract tests.
- Retryable writes carry an identity that the store enforces, and
  invalid input is never retried.
- A contract shared by separately deployed parts changes by expand,
  migrate, contract.
- For module layout, naming, and file structure, use
  `$write-readable-code`.

## Bundled tools

- `scripts/check_layers.py RULES.json [--root DIR]` reports disallowed
  imports, files in no layer, and import cycles; its tests are in
  `scripts/test_check_layers.py`.
- `assets/examples/orders/`: the domain, port, service, and three
  adapters, `layers.json`, and `tests/test_orders.py`.
- `assets/examples/protocols/`: LSP framing and position units, with
  tests.
- `assets/boundary-decision-example.md`: a worked multi-editor
  formatter decision.
- `sh assets/examples/verify.sh`.

## References

- [Architecture decisions](references/decisions.md)
- [Boundaries, ownership, and contracts](references/boundaries.md)
- [Protocols and pipelines](references/protocols-and-pipelines.md)

## Completion evidence

- Quality scenarios, each with the test or measurement that checks it.
- The decision record, with the rejected alternatives and their
  reasons.
- The `check_layers.py` output and the results of the contract tests.
- For contract changes, the parallel-change steps and where each one
  stands.
- Open decisions, and who needs to make them.

## Stop and ask

- Two teams or components claim the same state, and nobody has
  authority to decide.
- A quality requirement has no measure, and the choice depends on it.
- The change would split a deployment, or add a network hop, without a
  stated need.

[scenario]: references/decisions.md#quality-attribute-scenario
[adr]: references/decisions.md#decision-record-with-alternatives
[mps]: references/decisions.md#module-port-or-service
[queue]: references/decisions.md#direct-call-before-a-queue
[patterns]: references/decisions.md#pattern-only-for-a-named-boundary
[ui]: references/decisions.md#ui-state-with-its-owner
[truth]: references/boundaries.md#source-of-truth-map
[ports]: references/boundaries.md#ports-and-adapters
[contracts]: references/boundaries.md#contract-tests-shared-by-adapters
[direction]: references/boundaries.md#dependency-direction-check
[concurrency]: references/boundaries.md#adapter-owns-its-resources-concurrency
[idem]: references/boundaries.md#operation-identity-for-retries
[http]: references/boundaries.md#http-contract-with-problem-details
[parallel]: references/boundaries.md#parallel-change-for-two-sided-contracts
[lsp]: references/protocols-and-pipelines.md#lsp-framing-counts-bytes
[positions]: references/protocols-and-pipelines.md#position-encoding-negotiation
[lifecycle]: references/protocols-and-pipelines.md#lsp-lifecycle-and-document-ownership
[dap]: references/protocols-and-pipelines.md#debug-adapter-sessions
[pipelines]: references/protocols-and-pipelines.md#pipeline-contracts-by-kind
[host]: references/protocols-and-pipelines.md#host-adapter-around-a-portable-core
