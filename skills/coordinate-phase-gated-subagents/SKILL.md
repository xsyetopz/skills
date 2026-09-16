---
name: coordinate-phase-gated-subagents
description: >-
  Coordinates subagents through sequential requirements, design,
  implementation, integration/verification, and release phases using the
  Waterfall software development model. Use only for explicitly requested
  multi-agent execution with phase-completion checks. Parallel work stays
  inside the current phase. Not for plan-only requests or routine edits.
---


# Coordinate Phase-Gated Subagents

Coordinate multiple coding agents through a sequential software-development
lifecycle without allowing child agents to redefine the goal, skip required
phase evidence, or write concurrently to conflicting ownership. Use parallelism
only where independent work inside the current phase outweighs coordination
cost.

## Operating contract

- This skill is explicit-invocation-only. Do not start a multi-agent workflow
  merely because the harness supports subagents.
- The root user goal, authorized scope, constraints, and accepted baselines
  control every child assignment. A child proposal is evidence, not authority.
- Requirements, design, implementation, integration/verification, and release
  preparation are sequential lifecycle phases. Local TDD and refactoring remain
  valid cycles inside implementation.
- Assign disjoint write ownership or serialize dependent work. Do not merge
  conflicting child changes by selecting whichever looks plausible.
- Use zero or one proportionate independent review by default; add specialist
  reviews only for distinct material risks or explicit process requirements.
- A phase completes only when every required condition has corresponding
  evidence. Failed, unavailable, and unattempted checks remain distinct.

## Workflow

```mermaid
stateDiagram-v2
    [*] --> Requirements
    Requirements --> Design: requirements baseline accepted
    Design --> Implementation: design baseline accepted
    Implementation --> IntegrationVerification: implementation items integrated
    IntegrationVerification --> ReleasePreparation: required evidence passes
    ReleasePreparation --> [*]: authorized deliverable prepared
    Design --> Requirements: requirement change approved
    Implementation --> Design: design invalidated
    IntegrationVerification --> Implementation: defect requires code change
    ReleasePreparation --> IntegrationVerification: release evidence invalidated
```

## Procedure

1. Capture the exact root goal, authorized edit boundary, deliverable,
   acceptance conditions, existing process artifacts, harness capabilities, and
   project controls. Use the repository’s own issue/spec/plan formats rather
   than introducing a parallel lifecycle schema.
1. Determine whether multi-agent execution adds value. Partition by independent
   components, research domains, or distinct verification boundaries. Keep
   simple or tightly coupled work with one agent.
1. For the current phase, create bounded work items containing goal, source
   evidence, constraints, allowed files/actions, expected return shape, and stop
   condition. Verify effective model, tools, permissions, workspace,
   timeout/cancellation, and write ownership from the harness—not from the
   prompt alone.
1. Launch only ready, nonconflicting work. Reuse shared reconnaissance; do not
   make every child rediscover the same repository. Persist and inspect each
   completed result before it can be lost or superseded.
1. Integrate evidence and artifacts centrally. Check diffs, commands, outputs,
   and unresolved assumptions. Do not accept a child’s “done” label without the
   phase evidence or let a child commit, publish, deploy, reset, or expand scope
   unless explicitly authorized.
1. Apply the current phase gate. If a discovery invalidates an accepted earlier
   baseline, open a documented change decision, revise the earliest affected
   baseline, and repeat downstream checks rather than patching around the
   conflict.
1. Close or release child resources according to the harness. Deliver the
   integrated result and a truthful evidence summary; do not leave stale
   workers, worktrees, or unconsumed results.

## Read only the material needed

| Situation | Read or use |
| --- | --- |
| Defining and baselining requested behavior | [Phase 1 — requirements](references/phase-1-software-requirements.md) |
| Defining component, interface, ownership, and deployment decisions | [Phase 2 — design](references/phase-2-software-design.md) |
| Assigning and integrating implementation work | [Phase 3 — implementation](references/phase-3-software-implementation.md) |
| Integrating, verifying, and resolving defects | [Phase 4 — integration and verification](references/phase-4-software-integration-verification.md) |
| Preparing an authorized release deliverable | [Phase 5 — release preparation](references/phase-5-software-release.md) |
| Checking native subagent/model/cancellation capabilities | [Host capabilities](references/subagent-host-capabilities.md) |
| Partitioning work and protecting Git/workspaces | [Parallel assignment](references/parallel-software-work-assignment.md) |
| Revising accepted baselines after a late discovery | [Baseline change control](references/revise-software-phase-baselines.md) |
| Avoiding proliferation, duplicate work, lost results, and review ceremony | [Coordination failure modes](references/subagent-coordination-failures.md) |
| Using complete work-item and gate examples | [Worked examples](references/worked-examples.md) |
| Checking phase claims against evidence | [Verification and evidence](references/verification-and-evidence.md) |
| Reviewing source patterns and their limits | [Source index](references/source-index.md) |

## Additional specialized references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Adapt subagent methods from Bun’s software rewrite](references/bun-software-rewrite-methods.md) | Primary source: <https://bun.com/blog/bun-in-rust> (Jarred Sumner, July 8, 2026). |
| [Decision guide](references/decision-guide.md) | Use this guide after inspecting the target repository and current request. |
| [Domain model and authority](references/domain-model.md) | Current implementation is evidence of state, not automatically the desired contract. |
| [Enterprise operation and governance](references/enterprise-operation.md) | The skill may be used in repositories with protected branches, regulated data, separate owning teams, long support windows, and reproducible-build or audit requirements. |
| [Failure modes and recovery](references/failure-modes.md) | Preserve the first useful error and the state that produced it. |
| [Review software independently for evidenced defects](references/independent-software-review.md) | Defect-focused review checks software requirements, design, or implementation against evidence. |
| [Bundled resource catalog](references/resource-catalog.md) | Use this catalog to locate the exact skill-local files needed for the task. |
| [Decide whether a development phase may advance](references/software-phase-completion-criteria.md) | A phase gate is the required completion checks for the current development phase. |
| [Isolate subagent software edits and Git operations](references/subagent-workspaces-and-git-safety.md) | Parallel agents must not coordinate by destructively rewriting one shared working tree. |

## Evaluation cases

Use [evaluation cases](references/evaluation-cases.md) for realistic activation,
near-miss, and instruction-conformance probes. These are maintained test inputs,
not claimed results.

## Bundled executable helpers

- No bundled script is mandatory. Use the target repository’s established tools.

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- `assets/software-requirements-baseline.template.md`
- `assets/software-design-baseline.template.md`
- `assets/subagent-software-work-item.template.md`
- `assets/software-phase-completion.template.md`
- `assets/software-baseline-change-request.template.md`
- `assets/software-defect-review.template.md`
- `assets/software-requirement-verification.template.md`

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Accepted or explicitly unresolved requirements and design baselines in the
  project’s established format.
- A work partition with nonconflicting ownership, dependencies, and stop
  conditions.
- Consumed child results with inspected evidence and integrated artifacts.
- Phase-gate decisions tied to executed checks, source evidence, and unresolved
  limits.
- No open worker, workspace, or branch state left unintentionally.
- Release preparation only to the level authorized; publication or deployment
  requires separate authority.

## Stop or escalate

- Subagent execution, isolation, effective model/tool selection, or cancellation
  cannot be established for a risky task; serialize or perform the work locally.
- A material requirement, public contract, architecture, or policy decision
  remains user-owned.
- Required phase evidence is failed, unavailable, or unattempted.
- Concurrent ownership overlaps or a child changed the root goal.
- The coordination cost exceeds the value of parallelism.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
