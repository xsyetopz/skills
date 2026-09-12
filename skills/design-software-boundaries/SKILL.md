---
name: design-software-boundaries
description: >-
  Choose or review software architecture, patterns, paradigms, UI state flow,
  module boundaries, dependency direction, and structural migrations. Use for
  architecture decisions and demonstrated boundary problems, not routine edits.
---

# Design Software Boundaries

Answer the decision from evidence, not a pattern name. First state the
operation, data ownership, runtime/deployment model, quality-attribute
scenarios, team and consumer boundaries, state/failure model, and expected
evolution. Trace one representative operation in an existing system before
proposing a replacement. Separate requirements from assumptions.

Compare the smallest viable structure with only relevant alternatives. For each,
state the quality attribute improved, cost, assumptions, ecosystem support,
simpler alternative, overuse failure, and how to test, observe, and migrate it.
Prefer platform and framework facilities before custom infrastructure. A module,
direct call, native state mechanism, or sequential function chain is the default
until an independently deployed, versioned, concurrent, durable, or untrusted
boundary proves otherwise.

**DO NOT add an interface, factory, service, repository, event, schema version,
or protocol for a hypothetical future.** Add it only for a current alternate
implementation, extension axis, compatibility boundary, required isolation, or
platform contract. Do not make up quality attributes; turn them into measurable
scenarios first. Escalate long-lived multi-team operational concerns to
`$design-enterprise-software`.

## RED — DO NOT: choose pattern prestige for a local transform

**Deciding condition:** One desktop process reads one local file, transforms it
synchronously, and writes one output; no independent deployment or durable work
is required.

```text
UI -> controller -> service -> repository -> adapter -> event bus -> worker
```

Why RED:

- the local synchronous operation has no independent deployment or durable
  delivery requirement;
- every layer adds contracts and failure states without improving a stated
  quality attribute.

## GREEN — DO: use a boundary for each demonstrated force

```text
import/parse -> transform -> output
```

Why GREEN:

- one process, one local file, and synchronous work need neither an independent
  deployment nor durable delivery;
- each boundary represents distinct parse, transformation, or output behavior.

Check:

- run the normal path and one parse and write failure through the project's
  tests; add a job boundary only for actual recovery, scheduling, or isolation.

Read only the needed reference:

- [Architecture choices](references/architecture-choices.md) for system styles,
  quality scenarios, and boundary selection.
- [UI, paradigms, and principles](references/ui-paradigms-principles.md) for
  presentation state, language fit, and design principles.
- [Patterns and pipelines](references/patterns-pipelines.md) for recurring
  mechanisms, integration, concurrency, and pipeline semantics.
- [Language layout](references/language-layout.md) for cohesive modules,
  visibility, import/runtime boundaries, and package validation.
- [Service contracts](references/service-contracts.md) for independently
  deployed contracts and observability.
- [Ownership and migration](references/ownership-and-migration.md) for writers,
  idempotency, rollback, and ADRs.

For implementation, migrate authorized consumers, retire obsolete paths, and
verify dependency direction plus representative normal and failure paths. For a
design-only request, report the decision, rejected alternatives, assumptions,
and validation plan without scaffolding.
