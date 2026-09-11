---
name: design-software-boundaries
description: >-
  Choose or review software architecture, module and package layout, ownership,
  dependency direction, public contracts, and structural migrations. Use for
  from-scratch designs or demonstrated boundary problems, not routine edits that
  preserve existing boundaries or formatting-only changes.
---

# Design Software Boundaries

Trace the relevant code, consumers, state, and constraints. Identify the
boundary requiring different ownership, dependencies, lifecycle, transactions,
deployment, failure handling, or compatibility.

Separate established requirements from design assumptions. Do not turn missing
domain rules, data-loss policy, or failure semantics into requirements. Resolve
material uncertainty or label alternatives before committing to a design.

Choose the smallest structure that resolves the demonstrated problem. Define
authoritative writers, control of retries/cancellation, public inputs/outputs,
and failure semantics. Before designing a schema, protocol, config,
serialization, or compatibility mechanism, search for governing standards and
maintained ecosystem implementations, including the standard library. Verify
their fit and target versions. Reimplementing an established mechanism requires
a concrete unmet requirement, not a preference for dependency-free code. Do not
add version markers without an independently evolving compatibility boundary.

Read only the relevant reference:

- [Architecture choices](references/architecture-choices.md) for alternatives,
  maintenance and scaling costs, and a from-scratch decision procedure.
- [Language layout](references/language-layout.md) for cohesive modules,
  visibility, import/runtime boundaries, and package validation.
- [Ownership and migration](references/ownership-and-migration.md) for
  contracts, idempotency, generated provenance, rollback, and Nygard-style ADRs.

For implementation, migrate affected consumers and retire obsolete paths. Verify
dependency direction, representative state transitions, and changed generator
output with relevant project checks. Report the resulting ownership decision and
material unresolved risks. For a design-only request, provide the decision,
rejected alternatives, and validation plan without scaffolding an
implementation.
