---
name: plan-software-changes
description: >-
  Turns a request into requirements, an architecture decision, and a stepwise
  implementation plan with checked claims. Use before a multi-file change or a
  design choice.
---

# Plan Software Changes

Produce a plan another engineer or agent can execute without guessing. Models
fail here by asserting things about the codebase they never opened, by
inventing requirements nobody gave, and by writing steps nobody can verify.
Write only the parts the request needs: requirements, a decision, or a plan.

## Rules

- Verify every path, symbol, recipe, and command named in a plan against the
  repository before writing it down. Run each read-only verify command once
  and expect new-behavior checks to fail; list any that are destructive,
  publish, deploy, migrate, use the network, or need credentials as not
  run. Plans quote files that do not exist. Run
  `python3 scripts/audit_plan_claims.py`; a MISSING
  claim is acceptable only when an earlier task creates it.
- Do not invent requirements: timeouts, size limits, retention periods,
  retry counts, and policies nobody stated. Record each as an open decision
  (`DEC-...`) with options and what each costs, and ask. A plausible number
  reads as a decision.
- Give every requirement a source (request, issue, existing contract) and one
  response. Current behavior is evidence of constraints, not of intent; say
  which one a statement describes.
- Write acceptance criteria as observations at the contract boundary (Given,
  when, then: a return value, response, file, row, log line). "Works
  correctly" and "is fast" cannot fail; replace them with a measured value or
  a decision.
- Design for the stated need only. Add a port when two implementations exist
  now (a test double counts), a service only for an independent deployment or
  scaling need, a queue only when a direct call fails a named requirement.
- Give each piece of state one authoritative writer. A uniqueness, foreign
  key, or required-field rule is a database constraint; the code only turns
  the violation into a domain error.
- Make each task independently verifiable: `[depends: ...]`, `[files: ...]`,
  one `Verify:` command that exists, and an observable `Done when:`. Tasks such
  as "refactor the module" or "clean up as needed" fail this.
- Put tests that pass on current code before a change meant to preserve
  behavior, so a silent contract change fails a test.
- Give any step that changes data (migration, delete, rename, external
  notification) a rollback or an explicit "irreversible, because ..." line,
  and order it expand, migrate, contract. Never drop or overwrite before the
  copy is verified.
- Finish the replacement: if the plan adds a new path, include the task that
  removes the old path, flag, shim, TODO, or stub, with a grep that finds none
  at the end. Leaving both paths doubles the maintenance.
- Retries need an operation identity the store enforces; a read-modify-write
  of shared state needs an atomic or versioned write. Name the interleaving
  that breaks a step when you claim a flaw.
- Reviewing a plan: each finding cites the step, the violated constraint, a
  counterexample (a test or exact interleaving; say when argued, not run), and
  the smallest correction. Do not substitute your own design.
- Planning runs no commits, migrations, or deploys. Do not start
  implementing an approved plan unless asked.
- For module layout and naming, use `$improve-code-quality`.

## Workflow

1. Collect sources: the request and corrections, linked issues, existing
   contracts, and the code and commands the change touches. Note what must not
   change.
1. Requirements, if the request lacks them: glossary, then one EARS statement
   per response, acceptance criteria, open decisions.
1. Architecture, if a boundary or contract is being chosen: quality
   scenarios with measures, the choice, the rejected alternatives.
1. Plan: goal, out of scope, vertical-slice tasks in executable order.
1. Run `python3 scripts/audit_plan_claims.py PLAN.md REPO` and fix every
   MISSING or UNKNOWN claim, then re-read the plan as an execution asking what
   happens on failure, retry, and concurrent use.
1. Hand over the plan with the open decisions and the results of the commands
   you ran.

## Scripts

- `python3 scripts/audit_plan_claims.py PLAN.md REPO [--json]` checks named
  files, justfile recipes, `package.json` scripts, Makefile targets,
  Python modules, and programs. Exit 0 every claim found, 1 a claim
  missing, 2 bad input.
  Tested by `scripts/test_audit_plan_claims.py`. On Windows, use `py -3` for
  `python3`.

## References

- Read [`references/requirements.md`](references/requirements.md) when writing
  EARS statements, state or decision tables, measurable quality targets, or
  acceptance criteria and test mapping.
- Read [`references/architecture.md`](references/architecture.md) when choosing
  between module, port, service, or queue, recording a decision, or changing a
  contract shared by separately deployed parts.
- Read [`references/plans.md`](references/plans.md) when writing the task list,
  a migration, rollout, or estimate, or when reviewing a plan for flaws.
