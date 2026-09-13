---
name: plan-software-delivery
description: >-
  Create or revise evidence-based software delivery plans with deliverables,
  dependencies, estimates, milestones, risks, release readiness, and maintenance.
  Not for lifecycle selection or replacing native harness execution planning.
---

# Plan Software Delivery

Produce a delivery plan grounded in scope, dependencies, available capacity,
and uncertainty. Preserve the project's planning format and explicit
constraints.
Do not invent dates, staffing commitments, estimates, or stakeholder approvals.
A written delivery artifact does not replace native harness plans or goals;
use those mechanisms only under their own trigger and mode rules.
Do not publish issues, change hosted milestones, or implement the plan unless
those effects are separately requested.

## Establish the planning basis

Read requirements, current implementation, known defects, previous delivery
evidence, existing milestones, and release/support policy as relevant. Separate
required scope from options, assumptions, and unresolved decisions. Identify
who can accept each deliverable and what capacity is actually available; mark
unknown owners instead of assigning people without authority.

Break work into independently verifiable deliverables, including integration,
validation, migration, documentation, and operational preparation where needed.
Describe each result and acceptance criterion. “Backend 80% done” is not a
milestone; “new importer handles agreed fixtures through the packaged CLI with
no duplicate writes” can be one.

## Sequence and estimate

Record prerequisite artifacts and external dependencies, their owners where
known, lead times where evidenced, and what can proceed independently. Identify
dependency cycles and shared bottlenecks. Parallelizable work is not concurrent
capacity; account for specialist contention, review, test environments, and
support interruptions before projecting elapsed duration.

Read [estimation and risk](references/estimation-and-risk.md) when producing
estimates, comparing scenarios, or setting contingencies. Use observed analogous
work or a stated decomposition to justify ranges and assumptions. Separate
effort from elapsed time, target from forecast, and forecast from commitment.
Without evidence, leave an estimate unresolved and identify the measurement or
bounded investigation that would narrow it.

For an imposed date, assess feasible scope and confidence; do not backfill
optimistic estimates to make the arithmetic fit. Offer supported scope,
sequence, or risk trade-offs. Include uncertainty around external dependencies,
not only implementation effort.

## Milestones, risk, and progress

For each milestone, record accepted outputs, prerequisite evidence, owner if
known, forecast basis, and unresolved risks. Track progress through completed
artifacts and checks, not task count, code volume, or subjective percentages.
Compare observed throughput and blockers with the forecast; revise remaining
work when scope, capacity, or dependencies change and retain the reason.

Distinguish an active issue from a possible risk. For material risks, record
cause, consequence, likelihood/impact basis, warning signal, mitigation,
contingency, and owner where known. Do not invent probabilities. Schedule risk
reduction before the dependent irreversible commitment where practical.

## Release and continued ownership

Define release readiness from the actual contract: accepted behavior, supported
environment/package checks, artifact identity, migration/recovery evidence,
operator instructions, and unresolved-defect disposition. Include security or
compliance evidence only when applicable. Name rollback limits; “redeploy the
old binary” may not undo a data migration. Separate release readiness from
permission to deploy or publish.

Read [maintenance and change planning][maintenance] when scope includes ongoing
support, installed consumers, operational handover, or post-release changes.
Connect those obligations to capacity and future acceptance criteria instead of
treating maintenance as spare time after delivery.

Finish with deliverables, dependency order, estimate basis/ranges, milestone
acceptance, risk responses, release criteria, and maintenance obligations.
Check that each forecast has a basis, each dependency has a result or explicit
unknown, and no unconfirmed constraint became a commitment. State decisions
that block a reliable forecast separately from work that can proceed.

[maintenance]: references/maintenance-and-change-planning.md
