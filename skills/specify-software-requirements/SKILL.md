---
name: specify-software-requirements
description: >-
  Write or revise testable software requirements, scope, quality constraints,
  acceptance criteria, and traceability. Not for merely challenging a supplied
  plan or implementing requirements.
---

# Specify Software Requirements

Produce a specification that lets a reader distinguish acceptable behavior
from an incorrect implementation. Reuse the project's requirements format and
identifiers; a small change may need a few explicit criteria, not a new SRS.
Do not implement the specification or silently decide stakeholder conflicts.

## Establish intent and evidence

Identify the users, operators, affected external parties, and decision owners
relevant to the change. Read supplied requests, existing contracts, issue
discussions, and current behavior. Separate each source's stated need from your
inference; current code is not automatically the intended contract.

State the problem, desired outcome, system boundary, included capabilities,
excluded work, and external dependencies. Capture terminology where different
actors use the same word differently. Distinguish a mandatory constraint from
a preferred implementation. Ask only for missing decisions that materially
change scope or acceptance; mark undiscoverable facts and assumptions
explicitly.

## Write observable requirements

For each requirement, retain a stable ID where useful, its source/rationale,
priority, and observable acceptance evidence. Split independently negotiable
behavior; keep interdependent conditions together so exceptions remain visible.

- **Functional:** actor, trigger, preconditions, inputs, permitted action,
  result, and forbidden effects. Include empty/invalid input and failure paths
  that change the contract, not every imaginable defensive check.
- **Stateful:** initial state, event, guard, next state, persistent effect, and
  retry/cancel behavior. Identify terminal states and invalid transitions.
- **Interfaces:** producer/consumer, direction, data meaning and units,
  identity, version/compatibility constraints, errors, and ownership. Describe
  externally required semantics without inventing a new protocol.
- **Quality:** stimulus, workload/environment, measurable response, threshold,
  observation window, and measurement method. Cover performance, reliability,
  security, accessibility, or maintainability only where relevant to the need.
- **Constraints:** supported platforms, data handling, dependencies, budget or
  delivery constraints supplied by an authority. Label proposed values as
  proposals; do not fabricate regulatory obligations or stakeholder approval.

Replace “search is fast” with an agreed percentile, workload, dataset, hardware
class, and limit. If no limit is supplied, record “latency target unresolved”
and propose a baseline measurement; do not turn an illustrative 200 ms into a
commitment. For cancellation, specify whether an accepted operation may still
commit and how its final result can be discovered.

## Resolve feasibility and conflicts

Check whether available interfaces, resources, data, and supported environments
can meet the combined requirements. Separate known infeasibility from
uncertainty requiring a bounded prototype, measurement, or expert decision.
Propose such work with its deciding result; do not execute adjacent
implementation by default.

Rank needs by user impact, dependency, risk, and authoritative constraints, not
by calling every item mandatory. If offline writes conflict with immediate
global uniqueness, expose the trade-off and decision owner instead of promising
both. Record the chosen resolution only when supported; unresolved conflicts
remain visible in the specification.

## Acceptance and change impact

Map requirements to acceptance examples and planned verification boundaries.
Review normal, boundary, failure, and state-transition examples against sources.
Verification asks whether the specified contract is met; user acceptance asks
whether the result solves the intended task. A passing technical test does not
establish stakeholder acceptance.

Trace each changed requirement to affected interfaces, design decisions, tests,
documentation, and delivery dependencies when those artifacts exist. Mark
planned links rather than inventing completed artifacts. On revision, preserve
IDs and explain what changed, why, and which acceptance evidence is invalidated.

Finish with the specification, sources, assumptions, conflicts, and remaining
decisions. Check that each committed requirement is feasible or explicitly
qualified, internally consistent, and testable. Use interrogation for a
challenge-only request, architecture for structural choices, and delivery
planning for estimates and milestones; none is authorized merely by this skill.

Source: [NASA software requirements guidance][requirements] supplies coverage
considerations; NASA-specific mandated artifacts do not govern unrelated work.

[requirements]: https://swehb.nasa.gov/spaces/SWEHBVC/pages/50888900/SWE-050+-+Software+Requirements
