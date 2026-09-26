---
name: plan-implementation
description: >-
  Writes implementation plans as ordered tasks with files, verify commands,
  and done conditions, and reviews plans for flaws like unsafe order, lost
  updates, or no rollback. Use when planning a change or critiquing a plan.
  Not for requirements or executing plans.
---

# Plan Implementation

Produce plans another engineer or agent can execute without guessing, and
find the ways a plan fails before anyone executes it. Each task names its
files, its prerequisites, the command that proves it worked, and the
condition that makes it done; behavior is pinned by tests before it
changes; irreversible steps carry a rollback. A review walks the plan
against its constraints, audits its claims against the repository, and
proves each behavioral flaw with a counterexample. Both modes use the
same cards: each states how to write a construct and how to spot it done
wrong.

## Workflow

Write a plan for an agreed change:

1. Read the agreed requirements (IDs, acceptance criteria) and the current
   code, tests, and build commands the change touches. Note what must not
   change.
1. Write the goal and out-of-scope lines
   ([goal](references/plan-structure.md#goal-and-acceptance)).
1. List tasks as vertical slices; put tests that pin current behavior
   before the change they protect; add spikes where an unknown decides
   later tasks ([structure](references/plan-structure.md)).
1. For changes to shared interfaces or data, use expand, migrate,
   contract; add flags with removal tasks and rollbacks for irreversible
   steps ([delivery](references/delivery.md)).
1. Give every task `[depends: ...]`, `[files: ...]`, a `Verify:` command
   that exists in the repository, and `Done when:`.
1. Run `python3 scripts/check_plan.py PLAN.md` until it reports no
   defects; run each command from `--commands` at least once to confirm it
   exists and runs (on the base revision where the task pins behavior).
1. Add estimates with their basis and if-then risks only when a schedule
   or decision depends on them.
1. Review the draft with steps 2-5 of "Review a plan" and fix every
   finding; a MISSING claim is acceptable only for a file or command
   that an earlier task creates. Repeat until the review finds nothing
   else, then hand the plan over.

Review a plan:

1. Collect the plan, its requirements and constraints, the code it
   touches, and the deployment model
   ([inputs](references/review-method.md#inputs-to-collect)).
1. Run `python3 scripts/audit_plan_claims.py PLAN.md REPO` and record
   every MISSING or UNKNOWN claim; if the plan uses the task line format,
   also run `check_plan.py` on it.
1. Walk the plan as an execution, tracking state; at each step ask about
   failure, concurrency, retry, rollout, and irreversibility
   ([walk](references/review-method.md#walk-the-plan-as-an-execution)).
1. Match what you see to the cards in the table below.
1. For each behavioral flaw, build the counterexample (a test with a
   callback or barrier, or an exact interleaving); run it.
1. Write each finding with step, violated constraint, counterexample,
   minimal correction, and verification; order by severity
   ([format](references/review-method.md#finding-format)).
1. Separate optional suggestions from findings.

## Route the situation to a card

| Situation (writing, or seen in a plan under review) | Card |
| --- | --- |
| Starting the plan; a task does not trace to the goal | [Goal](references/plan-structure.md#goal-and-acceptance), [out of scope and scope creep](references/plan-structure.md#out-of-scope-and-scope-creep) |
| Writing tasks | [Task format](references/plan-structure.md#task-line-format), [verify](references/plan-structure.md#verify-command-per-task) |
| Done conditions; "done when it works" | [Done condition](references/plan-structure.md#done-condition-per-task) |
| Ordering tasks; a task uses something no earlier task creates | [Dependencies](references/plan-structure.md#dependencies-in-executable-order), [tests first](references/plan-structure.md#tests-before-the-change-they-protect) |
| Feature across layers | [Vertical slices](references/plan-structure.md#vertical-slices) |
| Unknown feasibility or performance | [Spikes](references/plan-structure.md#spikes-with-a-decision-rule) |
| Renaming a column, API field, or config key; lockstep change across separately deployed parts | [Expand and contract](references/delivery.md#expand-and-contract-migration) |
| Releasing behavior gradually | [Feature flag](references/delivery.md#feature-flag-with-removal-task) |
| Data migration, deletion, external notification | [Rollback](references/delivery.md#rollback-per-irreversible-step) |
| "How long will it take?" | [Estimates](references/delivery.md#estimates-from-analogies-with-ranges), [critical path](references/delivery.md#critical-path-and-elapsed-time) |
| Uncertainties that could change the plan | [Risks](references/delivery.md#risk-as-if-then-with-trigger), [updating from actuals](references/delivery.md#updating-the-plan-from-actuals) |
| Maintenance or support work | [Change classification](references/delivery.md#change-classification) |
| "Which process should we use?" | [Process choice](references/delivery.md#process-choice) |
| Read, modify, write back shared state | [Lost update](references/flaw-types.md#lost-update-between-read-and-write) |
| Write in place, delete before copy, drop before migrate | [Destructive ordering](references/flaw-types.md#destructive-failure-ordering) |
| "Retry on failure" | [Non-idempotent retry](references/flaw-types.md#non-idempotent-retry) |
| A step breaks a stated requirement | [Contradiction](references/flaw-types.md#contradiction-with-a-stated-constraint) |
| Files, commands, recipes named | [Claims mismatch](references/flaw-types.md#claims-that-do-not-match-the-repository), [claims audit](references/review-method.md#claims-audit) |
| Numbers or tool choices without a source | [Unsupported decision](references/flaw-types.md#unsupported-decision-or-invented-number) |
| Only the happy path | [Missing cases](references/flaw-types.md#missing-failure-and-boundary-cases) |
| Proving a flaw | [Counterexample as a test](references/review-method.md#counterexample-as-a-test) |
| Ranking and fixing findings | [Severity](references/review-method.md#severity), [minimal correction](references/review-method.md#minimal-correction), [non-findings](references/review-method.md#what-not-to-report-as-a-flaw) |

## Rules

- Precede a behavior-preserving change with tests that pass on the
  current code, so a silent contract change fails a test.
- No invented numbers: estimates cite their basis; unknowns become spikes
  or open decisions.
- Every finding quotes the step and the violated constraint, and has a
  concrete counterexample; "consider concurrency" is not a finding.
- Prove behavioral flaws by running a test or showing an exact
  interleaving; say when a finding is argued but not executed.
- Propose the smallest correction that removes the counterexample; do not
  replace the plan with your own architecture.
- Planning and review execute nothing: no commits, migrations, deploys,
  or plan steps against real systems.

## Bundled tools

- `scripts/check_plan.py PLAN.md [--commands]`: task format, unknown or
  later dependencies, cycles, vague verbs, critical path; `--commands`
  prints each Verify command.
- `scripts/audit_plan_claims.py PLAN.md REPO [--json]`: checks named
  files, justfile recipes, `package.json` scripts, Makefile targets,
  Python modules, and programs; exit 1 if any claim is missing.
- `assets/examples/count-delimiters/`: `delimiter-plan.md` (0 defects)
  with the `demo/` project its commands run against, `vague-plan.md`
  (defects including a cycle), and `verify.sh`, which checks both,
  audits the worked plan's claims, and runs its commands.
- `assets/examples/config-edits/`: `config-plan.md` (the plan under
  review), `review.md` (the finished review), `repo/` (counterexample
  tests for the lost update and destructive write, with corrections),
  and `verify.sh`, which runs the audit and the tests.

## References

- [Plan structure](references/plan-structure.md): read when writing or
  checking goal, out of scope and scope creep, task format, verify
  commands, done conditions, dependencies, tests first, vertical slices,
  spikes.
- [Delivery](references/delivery.md): read for changes to running systems
  or schedules: expand-contract migrations and lockstep changes, flags,
  rollback, estimates, critical path, risks, updates from actuals, change
  classification, process choice.
- [Flaw types](references/flaw-types.md): read when reviewing: lost
  updates, destructive ordering, retries, contradictions, repository
  claims, unsupported numbers, missing cases.
- [Review method](references/review-method.md): read when reviewing any
  plan, including your own draft: inputs, execution walk, claims audit,
  counterexample tests, finding format, severity, minimal corrections,
  non-findings.

## Completion evidence

A written plan passes `check_plan.py` with zero defects, and each
MISSING claim from `audit_plan_claims.py` names the earlier task that
creates it; the report lists the
critical path, each Verify command with the result of running it once
(or why it could not run yet), and any open decisions. A review lists
findings ordered by severity, each with step, constraint,
counterexample, correction, and verification; the claims audit output;
which counterexamples were executed (with commands) and which are argued
only; and a separate list of optional suggestions.
