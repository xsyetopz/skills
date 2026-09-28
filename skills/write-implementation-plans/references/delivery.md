# Delivery: migrations, rollout, estimates, and risk

Cards for plans that change running systems or need schedules. Where a
card also names a flaw, it says how to spot that flaw in a plan under
review.

## Contents

- Expand and contract migration
- Feature flag with removal task
- Rollback per irreversible step
- Estimates from analogies with ranges
- Critical path and elapsed time
- Risk as if-then with trigger
- Updating the plan from actuals
- Change classification
- Process choice

## Expand and contract migration

**Definition.** Change a shared interface (schema, API, config key) in
three phases so every intermediate deployment works: expand (add the new
form next to the old), migrate (move writers and readers, backfill data),
contract (remove the old form once nothing uses it)
([parallel change][parallel-change]). The flaw it prevents is a lockstep
change: the plan changes a schema, API, or message format and all its
consumers in one step, although they deploy independently.

**Use when.** Renaming or reshaping anything that other deployments,
services, clients, or stored data depend on.

**Do not use when.** The interface is private to one deployable unit that
changes atomically (one binary, one deploy).

**Example.**

```markdown
- T1 [depends: -] [files: migrations/0042_add_email_normalized.sql]
  Add nullable `email_normalized` and write both columns.
  Verify: `just db-test`
  Done when: new rows have both columns set.
- T2 [depends: T1] [files: scripts/backfill_email.py] Backfill old rows
  in batches of 1,000.
  Verify: `python3 scripts/backfill_email.py --dry-run --check`
  Done when: the check reports 0 rows with NULL `email_normalized`.
- T3 [depends: T2] [files: src/users/repository.py] Read from
  `email_normalized`.
  Verify: `just test users`
  Done when: no query reads `email`.
- T4 [depends: T3] [files: migrations/0043_drop_email.sql] Drop `email`
  after one release with no reads.
  Verify: `just db-test`
  Done when: the column is gone and all tests pass.
```

Flawed: "Rename the column and update the three services" in one task.

**Cost removed.** Downtime and failed deploys from lockstep changes.

**Verify.**

1. Each phase's Verify runs against a database or service in the previous
   phase's state, which tests the deploy order.
1. In review, ask which versions run together during rollout; a step
   that breaks any of them needs the three phases.

## Feature flag with removal task

**Definition.** New behavior ships behind a flag that is off by default
and enabled progressively. A planned task removes the flag once rollout
completes.

**Use when.** Behavior must be released and reverted independently of
deploys.

**Do not use when.** No task removes the flag; permanent flags accumulate
dead branches.

**Example.** `T5 [depends: T4] [files: src/flags.py, src/export.py]
Remove the export_cancel flag and its off branch.`

**Cost removed.** Deploy-to-revert cycles; forgotten flags.

**Verify.**

1. The plan contains a removal task for every flag it adds
   (`rg -n 'flag' PLAN.md`).

## Rollback per irreversible step

**Definition.** For each step that redeploying the previous version cannot
undo (data migrations, deletions, external notifications), the plan
states how to recover and rehearses it. Such a step without recovery or
rehearsal is a flaw.

**Use when.** Any step that changes stored data or external state.

**Do not use when.** "Revert the commit" is enough and the plan says so.

**Example.** "Rollback for T2: restore the `users` table from the snapshot
taken in T1b; rehearsed on staging with `just restore-staging`." Flawed:
"Drop the `email` column" with no backup or rehearsal task.

**Cost removed.** Improvised recovery during an incident.

**Verify.**

1. The backup or rehearsal command is itself a task with a Verify line,
   run on staging first.

## Estimates from analogies with ranges

**Definition.** Estimate from comparable finished work: name the source,
adjust for the differences, and give a range tied to named scenarios. A
low/high pair is not a statistical confidence interval
([GAO cost estimating guide][gao]).

**Use when.** A schedule or capacity decision depends on the plan.

**Do not use when.** The estimate would convert another team's story
points into hours or invent a velocity. In review, an estimate without a
basis is an
[invented number](flaw-types.md#unsupported-decision-or-invented-number).

**Example.** "T2 adapter: 2-4 days, based on the two previous provider
adapters (3 and 4 days); low if the sandbox is available on day 1, high
if it arrives in week 2 (waiting time not included)."

**Cost removed.** Dates nobody can defend or update.

**Verify.**

1. Each estimate names its basis; `[estimate: ...]` on every task lets
   the checker compute the critical path in hours.
1. In review, find the basis of each estimate or turn the unknown into a
   spike task.

## Critical path and elapsed time

**Definition.** The longest chain of dependent tasks sets the earliest
finish. Elapsed time includes waiting and contention, not just effort.

**Use when.** Parallelizing work or answering "when will it be done".

**Do not use when.** The date would sum all estimates as if one person
did them in series, or assume everyone is fully available.

**Example.** `check_plan.py` prints `critical path: T1 -> T2 -> T3 (3h)`
for the worked plan.

**Cost removed.** Promised dates that ignore the longest chain.

**Verify.**

1. Shortening the plan targets tasks on the printed path.

## Risk as if-then with trigger

**Definition.** "If <condition>, then <consequence>", with evidence for
likelihood and impact, a mitigation (reduces exposure now), a contingency
(the response if it happens), and the trigger that starts the
contingency.

**Use when.** An uncertainty could change scope, order, or dates.

**Do not use when.** A blanket percentage buffer would stand in for
addressing the specific unknown.

**Example.** "If the import format has undocumented fields, then data is
lost in migration. Mitigation: audit a 1,000-record sample in T1.
Contingency: defer the migration and decide scope. Trigger: any unmapped
field in the sample."

**Cost removed.** Surprises that were predictable.

**Verify.**

1. Each mitigation is a task or part of one; each trigger is observable.

## Updating the plan from actuals

**Definition.** At each milestone, compare finished work and blockers with
the estimates, update the remaining estimates and assumptions, and record
scope changes separately from estimation error.

**Use when.** A multi-day plan is in progress.

**Do not use when.** The update would redefine "done" to hit the date.

**Example.** "T2 took 5 days (estimate 2-4): sandbox arrived on day 3.
Remaining adapters re-estimated at 3-5 days."

**Cost removed.** Plans that drift from reality unnoticed.

**Verify.**

1. The plan's revision history shows actuals next to estimates.

## Change classification

**Definition.** Maintenance work is corrective (restore intended
behavior), adaptive (respond to environment changes), perfective (improve
capability or quality), or preventive (reduce evidenced future failure)
(ISO/IEC/IEEE 14764 categories).

**Use when.** Checking that a maintenance plan covers all obligations,
such as adaptive work for a runtime end-of-life.

**Do not use when.** It would create four backlogs, or label a speculative
rewrite "preventive".

**Example.** A renamed config key still used by supported installs gets
an adaptive compatibility task, a documented migration, and a retirement
decision based on consumer evidence.

**Cost removed.** Omitted compatibility and migration work.

**Verify.**

1. Each affected consumer, data format, and procedure has a task or an
   explicit decision.

## Process choice

**Definition.** Keep the team's existing workflow and add only the
practice that addresses an observed problem (an early slice for uncertain
user behavior, a spike for technical uncertainty, early integration for
coupled work).

**Use when.** The request asks how to organize the work.

**Do not use when.** It would prescribe a named methodology that nothing
in the context calls for.

**Example.** "Integrate the payments and ledger changes in T2 behind a
flag, because both teams depend on the shared schema."

**Cost removed.** Ceremony without benefit.

**Verify.**

1. Each added practice names the constraint it addresses.

[parallel-change]: https://martinfowler.com/bliki/ParallelChange.html
[gao]: https://www.gao.gov/products/gao-20-195g
