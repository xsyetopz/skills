# Plans

Read when writing the task list, a migration or rollout, or an estimate, and when reviewing a plan.
Follow the repository's own plan format when it has one (for example `docs/PLANS.md`); otherwise use
the task line below.

## Contents

- [Goal and scope](#goal-and-scope)
- [Task line](#task-line)
- [Order and slices](#order-and-slices)
- [Spikes](#spikes)
- [Data changes and rollback](#data-changes-and-rollback)
- [Flags](#flags)
- [Estimates and risk](#estimates-and-risk)
- [Reviewing a plan](#reviewing-a-plan)
- [Flaw patterns](#flaw-patterns)

## Goal and scope

State the observable outcome, what must stay the same, and where the requirement lives (IDs, issue).
Add an out-of-scope line; a task that does not trace to the goal is scope creep, so delete it or
move it to out of scope.

## Task line

```text
- T3 [depends: T1, T2] [files: app/x.py, tests/test_x.py] One-line summary.
  Verify: `python3 -m unittest tests.test_x`
  Done when: <observable condition>.
```

- `[depends: -]` marks a task with nothing before it. Dependencies point only to earlier tasks and
  never form a cycle.
- `Verify:` is one command that exists, run from the repository root. Run it once if it is
  read-only, and list it as not run if it writes data, migrates, or deploys; run it on the base
  revision for a task that pins current behavior.
- `Done when:` is observable: an exit code, a test name passing, a value, a diff grep. "Works",
  "cleaned up", and "improved" are not conditions.
- Verbs like "refactor", "handle", or "improve" without an object mean the task is not yet
  specified.
- Tag a task that rests on a report or inference (`[evidence: issue 12]`) or make it a spike.

## Order and slices

- Write vertical slices (one behavior across layers, shippable and testable) rather than horizontal
  layers that verify nothing until the last task.
- Put characterization tests first when behavior must not change: they pass on current code and pin
  its quirks (inline comments, case, duplicate keys, `%` interpolation for a config parser). Decide
  each quirk: keep or change, and record it.
- A task must not use something no earlier task creates. The audit script reports such paths as
  MISSING; a missing path is fine only when a task creates it and says so ("new", "create").
- A slice that leaves a TODO, stub, or placeholder names it, and a later `Done when:` removes it.
  The plan ends with a check (a diff grep for the markers it introduced) that finds none.
- Replacements finish the job: add the task that deletes the old function, flag, config key, and
  docs, not only the one that adds the new one.

## Spikes

When an unknown (feasibility, performance, an API's behavior) decides later tasks, add a time-boxed
spike with a decision rule: "if X, do T5; otherwise T6". Do not plan past the unknown with a guess.
An identity provider you have never used, with no sandbox access, is a spike and a blocked
dependency, not an estimate.

## Data changes and rollback

- Renaming or removing a column, field, or key that several parts use, and that deploy separately:
  expand (add new, write both), migrate (move readers and backfill), contract (drop old after
  evidence nothing reads it). A same-PR rename across services breaks whichever deploys second.
- Each step redeploying the old version cannot undo (migration, deletion, external notification)
  states how to recover and rehearses it: a snapshot or backup task with its own Verify, restore
  tried on staging. Without one, say the step is irreversible and why that is accepted.
- Never write in place, delete before copy, or drop before migrating: a failure in the middle leaves
  neither version.

## Flags

A feature flag comes with the task that removes it and the condition for removal, plus the rollback
(turn it off) and what that does to data already written under the new path.

## Estimates and risk

- Give an estimate only when a schedule depends on it, with its basis (a comparable past task, with
  its actual time) and a range. Unknowns make it conditional: "6 working days once credentials
  exist" is not a date.
- Write risks as if-then with a trigger and a response. Update the plan from actuals when a task
  overruns.

## Reviewing a plan

1. Collect the plan, its requirements, the code it touches, and how it is deployed (separate
   deploys, concurrent users, retries).
1. Run `scripts/audit_plan_claims.py PLAN.md REPO` and record every MISSING or UNKNOWN claim as a
   finding with the real name if one exists.
1. Walk the plan as an execution, tracking state. At each step ask what happens on failure midway, a
   retry, a concurrent writer, and rollout.
1. For each behavioral flaw build the counterexample: a test with a barrier or callback, or the
   exact interleaving. Run it or say it is argued only.
1. Write findings by severity: step, violated constraint, counterexample, minimal correction, how to
   verify. Keep optional suggestions separate. Do not report style preferences or alternative
   designs as flaws.

## Flaw patterns

- Lost update: read, modify, write of shared state (a cart, a counter). Two clients read the same
  value and the second write erases the first. Correct with an atomic operation, compare-and-set, or
  a version check.
- Non-idempotent retry: retrying a whole handler after the write succeeded but the reply failed
  repeats the write. Retry only before the write, or key the write by an identity.
- Destructive ordering: delete or overwrite before the replacement is verified.
- Contradiction: a step breaks a stated requirement or must-not-change line.
- Claims that do not match the repository: a recipe, script, or path that is not there
  (`just test-cart` with no such recipe).
- Unsupported decision: a number or tool choice with no source.
- Happy path only: no failure, empty, or boundary case in any task.
- Unremoved marker: a TODO or stub no task removes.
