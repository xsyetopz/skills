# Phase 1: specify software requirements

Goal: freeze **what must be true**, independent of implementation choice.

## Inputs

Inspect the user's request, existing behavior, public interfaces, compatibility
contracts, relevant standards, tests, operational constraints, performance
baselines, security requirements, and explicitly excluded scope.

For a rewrite or migration, treat the current system as evidence, not as the
requirements source of truth. Existing bugs may be behavior to fix rather than
behavior to preserve.

## Parallel analysis

Parallelize source discovery by independent evidence domain, for example:

- public/API behavior;
- CLI/file/protocol compatibility;
- performance and resource constraints;
- build/deployment environment;
- security and safety constraints;
- existing test coverage and known gaps.

Each analyst returns candidate requirements with source/evidence and conflicts.
Only the phase integrator assigns canonical identifiers and edits the baseline.

## Requirement record

Each requirement must contain:

- stable ID (`REQ-...` or the project's native identifier);
- statement with one observable obligation;
- source/rationale;
- priority or mandatory/optional status when the project already distinguishes
  it;
- acceptance condition;
- verification method: test, analysis, inspection, measurement, or
  demonstration;
- dependencies/conflicts;
- explicit non-goal when confusion is likely.

Avoid implementation language unless the implementation choice is itself a
constraint.

## Phase completion check

Advance only when:

- scope and non-goals are explicit;
- requirements are internally consistent;
- externally visible compatibility obligations are enumerated;
- every mandatory requirement has a feasible verification method;
- unresolved unknowns are closed or explicitly accepted as requirements-phase
  risk;
- the verification matrix has entries for every mandatory requirement;
- no design or implementation choice is used to hide a missing requirement.

Freeze the requirements baseline and record its version/hash.
