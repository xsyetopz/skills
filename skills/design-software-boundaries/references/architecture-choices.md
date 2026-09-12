# Choose architecture from constraints

These are engineering decision criteria, not a mandatory architecture. Assume
the result must be maintained unless the user explicitly requests a throwaway.

## Establish the decision

Identify the real operations, data owners, durability and consistency needs,
latency/throughput targets, deployment environment, trust boundaries, team
ownership, and supported consumers. Separate measured constraints from
forecasts. For an existing project, trace one representative operation before
proposing a replacement. For a new project, use ecosystem-native packaging and
the smallest complete vertical feature; do not generate every prospective
subsystem.

Record what the current structure cannot do. Compare keeping it, a local
boundary change, and a larger alternative only when relevant. Include
implementation, operating, migration, and cognitive costs. A framework's name is
not evidence that these costs are justified.

## Compare relevant alternatives

### Cohesive modules in one deployment

Useful when: features share transactions and release cadence.

Cost: hidden cross-module writes can destroy ownership.

Simpler alternative: functions and types in an existing module.

### Layers

Useful when: presentation, policy, and storage have distinct responsibilities.

Cost: pass-through layers and changes spread across every layer.

Simpler alternative: a feature module with private helpers.

### Ports/adapters

Useful when: a consumer needs a stable boundary against external systems.

Cost: translation and contract maintenance; wrappers can leak provider
semantics.

Simpler alternative: direct use of the existing client behind a local function.

### Pure computation plus I/O orchestration

Useful when: policy or transforms can operate on explicit inputs.

Cost: copying large state or encoding every effect can outweigh testability.

Simpler alternative: extract only the computation that benefits.

### Pipeline

Useful when: stages transform well-defined intermediate data.

Cost: buffering, backpressure, partial failure, and lost provenance.

Simpler alternative: sequential function calls before queues or processes.

### State machine

Useful when: legal transitions and cancellation/order are the hard part.

Cost: duplicated state and transition explosions.

Simpler alternative: a native enum and explicit transition function.

### Event-driven consumers

Useful when: independent reactions or delayed processing are required.

Cost: ordering, duplicate delivery, replay, and eventual consistency.

Simpler alternative: a direct call or transaction.

### Separate services

Useful when: independent deployment, isolation, or scaling is necessary.

Cost: network failure, contract evolution, operations, and cross-service
consistency.

Simpler alternative: modules in the same deployment.

### Data-oriented storage

Useful when: profiles show hot traversal or locality costs.

Cost: harder updates and indexing; duplicated representations.

Simpler alternative: improve one hot data structure before changing the domain
model.

The cloud-specific [Microsoft architecture catalog][styles] explains why layers,
workers, events, and services have different deployment and consistency costs.
Do not infer that a non-cloud application needs cloud infrastructure.

An actor/message-passing design can assign mutable state to one owner. Verify
the chosen runtime's mailbox limits, ordering, reentrancy, supervision,
persistence, and cancellation semantics before relying on them. An actor does
not by itself make external effects transactional. A bounded queue and one
worker may suffice.

For FFI, plug-ins, and RPC, discover the actual ABI/protocol, allocator and
resource ownership, threading, and compatibility rules. Do not exchange native
object layouts across independently compiled or untrusted components without a
verified contract. Reuse the platform's existing interface before inventing a
wire format.

## Evaluate the actual dependency boundary

Treat ecosystem catalogs as discovery leads, not verified adoption decisions.
Labels such as maintained, lightweight, pure-managed or compiler-independent do
not establish compatibility. Check the selected version's manifest,
implementation, license, support/security status, transitive features and
deployment requirements. Prefer an existing dependency or platform facility when
it meets the contract; compare concrete alternatives only where there is an
unmet need.

Do not confuse an interface with its implementation. Go's `database/sql`
provides the common API but requires a separate driver: it cannot replace a
SQLite driver by itself. If CGO is forbidden, verify the chosen driver's
supported path with `CGO_ENABLED=0` build and test runs. This does not prove
independence from native runtime libraries or subprocesses. A CGO-free
implementation such as `modernc.org/sqlite` still has its own supported targets
and dependency cost. [SQL contract][go-sql], [CGO][go-cgo], [driver
documentation][go-sqlite].

For Rust, evaluate the resolved feature graph, not just a direct dependency's
`default-features = false`. Features can be enabled by another consumer. Inspect
`cargo tree -e features` and the selected TLS, async, native-library and target
paths; do not assign one dependency-cost or portability label to every build of
a crate. Respect the workspace's MSRV and `no_std` requirements when considering
standard-library replacements. [Cargo features][cargo-features].

For .NET, distinguish the inbox API from the application's serialization and
publication mode. `System.Text.Json` source generation can support constrained
reflection/AOT paths, but the actual types, options and overloads must use the
generated metadata. Verify the affected published artifact; a catalog's AOT
rating is not a substitute. [JSON source generation][json-sourcegen].

For TypeScript, separate consuming declarations from running a compiler-API
client. A generator can emit compatible types while requiring a different
compiler API internally. For example, the inspected `openapi-typescript` 7.13.0
package declares a TypeScript 5 peer and calls its AST factory API; it is not
compiler-independent merely because its input is OpenAPI. Check actual package
metadata and generation under the chosen toolchain. If a separate generator
workspace is justified, keep that boundary explicit rather than silently
replacing the application's compiler or configured lint rules. [Generator
source][ts-generator], [package metadata][ts-package].

## System-style coverage

Use these labels to compare a demonstrated force; none is a target state. For
one candidate, make a quality-attribute scenario with stimulus, environment,
expected response, and measure before selecting it.

- **Modular monolith:** use for one release, shared transactions, and cohesive
  ownership. It reduces operations and preserves local consistency. Its cost is
  hidden cross-module coupling. Start with a cohesive feature module; do not
  split deployables merely to claim scale.
- **Layered:** use when presentation, policy, and data change separately. It
  separates concerns but pass-through layers spread changes. A feature module is
  simpler; empty service/repository layers add indirection.
- **Ports/adapters, hexagonal, onion, clean:** use when application policy needs
  protection from a real external contract. Translation and contract maintenance
  are costs. Use a local wrapper or direct client when there is no such
  boundary.
- **Client/server and SOA:** use when remote ownership or coarse business
  capabilities cross organization boundaries. They centralize authority and
  interoperability at the cost of network, security, and governance work. A
  modular monolith with explicit ownership is simpler when deployment is shared.
- **Microservices:** use for independent deployment, fault isolation, scaling,
  or lifecycle per capability. They add distributed consistency, contracts,
  observability, and operations. A module is simpler; services are not folders.
- **Event-driven:** use when independent reactions or delayed work require
  decoupling. It adds ordering, duplicates, replay, and eventual consistency.
  Use a direct call or transaction for local synchronous control flow.
- **Actor/message passing:** use when concurrent mutable state needs one owner.
  It adds mailbox, supervision, and external-effect complexity. A mutex plus
  bounded worker may suffice.
- **Pipes and filters:** use for stable intermediate representations. It adds
  buffering, provenance, and partial-failure concerns. Sequential calls are
  simpler.
- **Plugin/extension:** use for independently delivered code along one defined
  axis. It requires ABI, isolation, compatibility, and security policy. Use
  configuration, a callback, or a built-in strategy when those meet the need.
- **Serverless/event handler:** use for intermittent, short-lived work with
  suitable platform triggers. Cold starts, timeouts, and platform coupling are
  costs. A process is simpler for stateful or long-running work.
- **Data-intensive/distributed:** use only when measured volume, availability,
  regional, or throughput constraints exceed one owner/store. Replication and
  coordination cost more than optimizing an authoritative schema/query/cache.

Quality attributes are not adjectives. Example: “During a 30-second dependency
outage, accepted writes are rejected within two seconds or retained for replay
without duplication.” Evaluate alternatives against this scenario, not “high
reliability.” ATAM-style evaluation exposes risks, sensitivity points, and
trade-offs; it is not required ceremony for small work.

Sources: [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html),
[SEI ATAM collection][sei-atam],
[Azure architecture styles][azure-styles],
[AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/).

## Work one feature end to end

Example: a small team's report service reads one database and produces CSV.
Start with the established HTTP/CLI entrypoint, a report query, and the
maintained CSV writer already used by the project. A module can own the query
and output semantics without a repository interface, custom file format, event
bus, or separate deployment. Tests parse output with an independent CSV reader
and cover quoting, empty results, and permission failures.

If measured runtime exceeds the request deadline, compare query optimization and
streaming with a durable job. A job needs persisted status, an authorization
boundary, cancellation semantics, and a verified queue's delivery contract. That
is a new operational commitment, not a cosmetic extraction. Define how to
recover after a worker stops between storing the result and acknowledging work.

Validate the selected boundary with a representative consumer and its failure
path. For a migration, identify rollback limits and remove the superseded path
after supported consumers move. For a design-only task, specify these checks
without building a proof-of-concept unless requested.

[styles]:
  https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/
[go-sql]: https://pkg.go.dev/database/sql
[go-cgo]: https://pkg.go.dev/cmd/cgo
[go-sqlite]: https://pkg.go.dev/modernc.org/sqlite
[cargo-features]: https://doc.rust-lang.org/cargo/reference/features.html
[json-sourcegen]:
  https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/source-generation
[ts-generator]:
  https://github.com/openapi-ts/openapi-typescript/blob/main/packages/openapi-typescript/src/lib/ts.ts
[ts-package]: https://registry.npmjs.org/openapi-typescript/7.13.0
[sei-atam]:
  https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
[azure-styles]:
  https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/
