---
name: define-requirements
description: >-
  Use when essential behavior for a requested system change needs explicit
  inputs, outputs, state transitions, failure outcomes, constraints, and
  acceptance criteria. Distinguish desired behavior from existing behavior. Not
  for choosing an architecture or rewriting complete requirements.
---

# Define Requirements

Turn an agreed outcome into observable, testable behavior and constraints
without stealing product decisions, choosing implementation, or inventing
thresholds. Requirements define what must hold at interfaces and state
transitions; design and planning decide how to build it.

## Operating contract

- Inspect the request, current behavior, public interfaces, support policy,
  issue/spec context, and relevant user corrections before drafting.
- Separate desired behavior from current state and from a hypothesis about the
  cause of a defect.
- Use domain terms and explicit units. Do not invent timeouts, limits,
  compatibility ranges, actors, approvals, or nonfunctional thresholds.
- State preconditions, inputs, outputs, side effects, errors, state transitions,
  concurrency/cancellation behavior, and observability only where material.
- Acceptance criteria must discriminate the requested behavior; they are not
  implementation prose or a preferred class/file layout.

## Requirement-authoring contract

- Treat the user goal, scope, approval boundary, and required evidence as
  controlling. This skill narrows how to produce a behavioral requirement set;
  it MUST NOT broaden authority or override repository instructions.
- For GPT-5.6 and GPT-6, provide actors, inputs, outputs, state, failures,
  constraints, and unresolved decisions, hard constraints, available tools, and
  the finish condition once. Remove repeated directions and examples unless a
  recorded evaluation shows that they prevent a real failure.
- Infer routine, reversible steps from inspected evidence. Ask only when an
  unresolved choice changes an external contract. Stop before an external write,
  destructive action, credential use, or material scope expansion that the user
  did not authorize.
- Load a linked reference only when its subject affects the current decision.
  Use scripts for deterministic mechanics; use model judgment for semantic
  decisions. Inspect tool output before relying on it.
- Validate at the boundary of the claim with examples, counterexamples,
  traceability, and acceptance checks. Report commands, observed results, and
  gaps. A parser, build, or single green test proves only the property that it
  can discriminate.
- Use **MUST** only for an absolute safety or interoperability requirement,
  **SHOULD** for a default with valid exceptions, and **MAY** for an option.
  Write short active sentences and use one stable term for each concept. This
  style is STE-inspired; it is not a claim of formal ASD-STE100 conformance.

## Workflow

```mermaid
flowchart TD
    G[User outcome] --> S[Inspect current contracts and evidence]
    S --> Q{Material decision unresolved?}
    Q -->|Yes| O[Present concrete options and consequences]
    Q -->|No| C[Define behavior contract]
    O --> C
    C --> A[Write observable acceptance criteria]
    A --> T[Trace criteria to sources and affected boundaries]
    T --> R[Review for invented scope and implementation leakage]
```

## Procedure

1. Capture the exact requested outcome and authorized scope. List source
   statements and corrections that control the requirement. Inspect existing
   public behavior and support policies only to identify constraints, not to
   assume the current implementation is intended.
1. Identify actors/systems, trigger, preconditions, input domain, required
   outputs/effects, failure outcomes, and state transitions. Use one consistent
   domain vocabulary and units.
1. Surface material choices the evidence does not decide—for example overwrite
   policy, ordering guarantee, compatibility, retention, authorization, or
   external error mapping. Provide options with consequences rather than
   silently choosing.
1. Write atomic requirements in declarative language. Separate functional
   behavior, data/integrity constraints, security/authorization,
   performance/capacity, operability, compatibility/migration, and out-of-scope
   items only where relevant.
1. Write acceptance criteria as observations at the contract boundary. Include
   representative success, boundary, failure, cancellation/concurrency, and
   rollback/recovery cases when those behaviors are part of the request.
1. Trace each requirement to a user statement, public contract, authoritative
   external interface, or explicit decision. Mark assumptions and unresolved
   decisions; do not disguise them as requirements.
1. Review for implementation leakage, duplicated statements, unverifiable
   adjectives, invented numbers, example-as-requirement, and conflict with prior
   corrections. Deliver in the repository's existing issue/spec format.

## Choose the behavior-model reference

| Situation | Read or use |
| --- | --- |
| Checking behavior, failure, state, and acceptance completeness | [Contract checks](references/contract-checks.md) |
| Choosing how much specification the task needs | [Operational decisions](references/behavioral-requirements-operational-decisions.md) |
| Using complete requirement examples for APIs, async work, and data changes | [Worked scenarios](references/behavioral-requirements-worked-scenarios.md) |
| Checking criterion-to-claim evidence | [Verification and claim evidence](references/behavioral-requirements-verification-and-claim-evidence.md) |
| Avoiding implementation leakage and invented constraints | [Failure patterns and recovery](references/behavioral-requirements-failure-patterns-and-recovery.md) |
| Applying enterprise authority, traceability, and change control | [Organizational controls and scale](references/behavioral-requirements-organizational-controls-and-scale.md) |
| Using the export/cancellation example | [Export cancellation specification](assets/export-cancellation-spec.md) |
| Checking requirements sources | [Standards, APIs, and authorities](references/behavioral-requirements-standards-apis-and-authorities.md) |

## Requirement decision references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Concepts, contracts, and invariants](references/behavioral-requirements-concepts-contracts-and-invariants.md) | Use when distinguishing the requested behavioral requirement set from observed repository state. |
| [Bundled resource map](references/behavioral-requirements-bundled-resource-map.md) | Use when locating bundled resources for the behavioral requirement set. |

## Behavioral evaluation

Run [the maintained Agent Skills evaluations](evals/evals.json) in clean
target-client contexts. Compare this revision with a no-skill or prior-skill
baseline. Review commands, diffs, and artifacts; do not grade prose alone. The
checked-in cases are test inputs, not claimed results.

## Bundled executable helpers

- No bundled script is mandatory. Use the target repository's established tools.

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- `assets/export-cancellation-spec.md`

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Scope and authoritative inputs.
- Functional and relevant nonfunctional requirements with consistent
  terminology.
- Explicit unresolved material decisions and assumptions.
- Observable acceptance criteria mapped to each requirement.
- Out-of-scope behavior and preserved existing contracts.
- Traceability to user statements, public contracts, or approved decisions.

## Stop or escalate

- A material product, public-API, compatibility, legal, or policy decision
  remains unresolved.
- The requested behavior depends on a threshold or support range that no
  authoritative source defines.
- The task asks only for implementation of already complete requirements.
- The available evidence cannot distinguish desired behavior from current
  accidental behavior.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
