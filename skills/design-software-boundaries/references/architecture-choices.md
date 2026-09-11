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
