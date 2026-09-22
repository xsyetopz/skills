---
name: remove-unneeded-compatibility-code
description: >-
  Use when removing compatibility aliases, shims, fallbacks, or version branches
  shown to be unnecessary: support invented without a requirement, or support
  explicitly retired. Trace callers, persisted data, and declared public
  contracts first. Age, a failing test, or an empty search alone does not
  authorize deletion.
---

# Remove Unneeded Compatibility Code

Remove compatibility behavior only after classifying its authority and
consumers. Distinguish never-required agent-invented support from legitimate
support that has been formally retired, and preserve real public,
persisted-data, deployment, and external-consumer obligations.

## Operating contract

- Do not equate “legacy,” old, unused locally, ugly, failing, or covered by a
  test with unneeded. Establish the support authority.
- Classify each behavior as required, never required, explicitly retired, or
  unresolved. Existing code/tests do not decide the category by themselves.
- Trace internal callers, public consumers, serialized data, configuration,
  CLI/API names, plugin/provider contracts, package exports, docs, migrations,
  and operational tooling.
- Remove the full obsolete path—registration, dispatch, tests, docs, packaging,
  feature flags, telemetry, and migration state—without deleting unique required
  validation, cleanup, or error behavior.
- Do not reintroduce the same behavior under a synonym, catch-all fallback, or
  “temporary” alias.

## Compatibility-retirement contract

- Treat the user goal, scope, approval boundary, and required evidence as
  controlling. This skill narrows how to produce a compatibility removal; it
  MUST NOT broaden authority or override repository instructions.
- For GPT-5.6 and GPT-6, provide declared support policy, external consumers,
  persisted data, aliases, fallbacks, version branches, and unique wrapper
  behavior, hard constraints, available tools, and the finish condition once.
  Remove repeated directions and examples unless a recorded evaluation shows
  that they prevent a real failure.
- Infer routine, reversible steps from inspected evidence. Ask only when an
  unresolved choice changes an external contract. Stop before an external write,
  destructive action, credential use, or material scope expansion that the user
  did not authorize.
- Load a linked reference only when its subject affects the current decision.
  Use scripts for deterministic mechanics; use model judgment for semantic
  decisions. Inspect tool output before relying on it.
- Validate at the boundary of the claim with consumer searches, contract tests,
  migration checks, and before/after behavior. Report commands, observed
  results, and gaps. A parser, build, or single green test proves only the
  property that it can discriminate.
- Use **MUST** only for an absolute safety or interoperability requirement,
  **SHOULD** for a default with valid exceptions, and **MAY** for an option.
  Write short active sentences and use one stable term for each concept. This
  style is STE-inspired; it is not a claim of formal ASD-STE100 conformance.

## Workflow

```mermaid
flowchart TD
    C[Compatibility behavior] --> A[Identify authority and support policy]
    A --> U[Trace callers, consumers, persisted data, and deployment]
    U --> K{Classification}
    K -->|Required| P[Preserve]
    K -->|Unresolved| Q[Surface decision / gather evidence]
    K -->|Never required| R[Remove within authorized scope]
    K -->|Explicitly retired| R
    R --> V[Verify supported paths and absence of fallback]
    V --> D[Update docs/package/config/migrations as needed]
```

## Procedure

1. Name the exact alias, shim, fallback, version/platform branch, deprecated
   API, package export, config key, or data compatibility behavior. Record its
   current implementation and claimed purpose.
1. Find authority: current request, declared stable public contract,
   version/deprecation policy, release history, migration decision, supported
   platform/version matrix, and owner decisions. Do not let an agent-added test
   create its own support mandate.
1. Trace consumers using source search, history, generated/source relationships,
   package/export metadata, telemetry where approved, docs, downstream
   repositories where available, persisted/serialized data, deployment config,
   and runtime registration. Treat absent local references as unknown for
   external public surfaces.
1. Classify required, never required, retired, or unresolved. If unresolved and
   externally meaningful, stop for a decision. Do not invent a deprecation
   period or migration for support that never existed.
1. Remove the obsolete path and only its dependent artifacts. Preserve
   validation, errors, cleanup, and shared implementation used by supported
   paths. Remove registrations and packaging that would silently keep the
   behavior alive.
1. Update or remove tests according to the actual contract. Add negative checks
   for removed public aliases only when rejection behavior is part of the
   contract. Ensure supported inputs still work and unknown inputs fail
   explicitly.
1. Run package/API/serialization/migration/integration checks appropriate to the
   surface. Inspect artifact exports and runtime registration. Report
   consumers/evidence, classification, changes, and remaining uncertainty.

## Choose the consumer-evidence reference

| Situation | Read or use |
| --- | --- |
| Tracing authority, consumers, data, and complete removal | [Removal evidence](references/removal-evidence.md) |
| Classifying required, never-required, retired, and unresolved support | [Operational decisions](references/compatibility-retirement-operational-decisions.md) |
| Using API, CLI, config, data, and platform examples | [Worked scenarios](references/compatibility-retirement-worked-scenarios.md) |
| Verifying removal and supported behavior | [Verification and claim evidence](references/compatibility-retirement-verification-and-claim-evidence.md) |
| Avoiding empty-search, test-as-spec, and alias-reintroduction errors | [Failure patterns and recovery](references/compatibility-retirement-failure-patterns-and-recovery.md) |
| Applying enterprise version/support governance | [Organizational controls and scale](references/compatibility-retirement-organizational-controls-and-scale.md) |
| Checking SemVer/package export sources | [Standards, APIs, and authorities](references/compatibility-retirement-standards-apis-and-authorities.md) |

## Compatibility decision references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Concepts, contracts, and invariants](references/compatibility-retirement-concepts-contracts-and-invariants.md) | Use when distinguishing the requested compatibility removal from observed repository state. |

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

- No output template is mandatory. Preserve the repository's established format.

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Exact compatibility behavior and all implementation/registration/package
  surfaces.
- Authority and consumer evidence with one of four classifications.
- Scoped removal or explicit preservation/unresolved decision.
- Updated tests/docs/package/config/migration artifacts required by the actual
  contract.
- Executed supported-path and absence/rejection verification.
- Remaining external-consumer or persisted-data uncertainty.

## Stop or escalate

- A declared stable/public or persisted-data consumer may exist and available
  evidence cannot resolve it.
- The support decision belongs to the user/product owner and has not been made.
- Removal would affect another package/repository/system outside authorized
  scope.
- The behavior contains unique required validation, cleanup, or error handling
  not yet relocated safely.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
