---
name: coordinate-phase-gated-subagents
description: >-
  Runs a Waterfall delivery with subagents: requirements, design,
  implementation, verification, and release phases with evidence-based gates
  and parallel worktree waves. Use only when the user explicitly asks for
  phase-gated or Waterfall coordination.
---

# Coordinate Phase-Gated Subagents

Run a multi-agent delivery in which each phase closes on evidence,
workers stay inside their owned paths, and the user's goal controls
every assignment. `assets/examples/verify.sh` shows the two checkers
and a git worktree integration.

## Workflow

1. Confirm that the user explicitly asked for phase-gated multi-agent
   work. If not, do the task directly: the ceremony costs more than a
   single agent for small tasks. Map the host's features before
   promising parallelism ([host capabilities][host]).
1. Phase 1: write the requirements baseline, with IDs, acceptance
   conditions, and verification methods ([requirements][p1]). Close
   its gate.
1. Phase 2: write the design baseline and the work plan, with owned
   paths and dependencies ([design][p2]). Run
   `python3 scripts/check_work_items.py PLAN.json` until it passes.
   Close the gate.
1. Phase 3: spawn one wave at a time, with complete briefs
   ([brief][brief]) in isolated worktrees ([isolation][worktrees]).
   Accept a result only when it has evidence and stays in scope
   ([results][results]). Optionally, spawn one independent reviewer per
   unit ([review][review]).
1. Phase 4: integrate in the planned order, partition failures by owner
   and cause, and fill in the verification matrix ([verification][p4]).
1. Phase 5: prepare the release from the verified revision. Publish
   only with explicit approval ([release][p5]).
1. At every gate, run `python3 scripts/check_gate.py GATE.json`, and
   keep the gate open until it passes ([gates][gates]). Changes to a
   frozen baseline go through a change request that reopens every
   downstream gate ([change][change]).

## Route the situation to a card

| Situation | Card |
| --- | --- |
| Which host features exist | [Host capabilities][host] |
| Writing requirements | [Phase 1][p1] |
| Breaking work into items | [Phase 2][p2], [waves][waves] |
| Spawning workers | [Brief][brief], [phase 3][p3] |
| Parallel edits | [Worktree isolation][worktrees] |
| Worker says "done" | [Result contract][results] |
| Reviewing a unit | [Independent review][review] |
| Integration failures | [Phase 4][p4], [failure diagnosis][diagnosis] |
| May we move on? | [Gate decision][gates] |
| Requirement or interface must change | [Change request][change] |
| Release | [Phase 5][p5] |

## Rules

- The user's goal and the frozen baselines control each assignment. A
  worker's proposal is evidence, not authority.
- Parallel items must pass `check_work_items.py`: no shared owned
  paths, and no items from another phase.
- Workers write only in their owned paths and their own worktree, and
  never run destructive git commands. The orchestrator integrates.
- A gate closes only on passed evidence with commands. Keep failed,
  unavailable, and not-run evidence distinct.
- Never weaken a check to make it pass.
- Publishing, pushing, and deploying need explicit user approval.

## Bundled tools

- `scripts/check_work_items.py PLAN.json [--json]` reports errors and
  parallel waves. It exits 0 when the plan is safe.
- `scripts/check_gate.py GATE.json` exits 0 when the gate may close,
  and 1 with the reasons when it may not.
- `scripts/test_checks.py` tests both checkers.
- `assets/examples/`: a good and a conflicting work plan, a closing
  and an open gate record, and `verify.sh`.
- Templates in `assets/`:
  - requirements baseline;
  - design baseline;
  - work item;
  - defect review;
  - requirement verification;
  - phase completion;
  - baseline change request.

## References

- [Phases and gates](references/phases-and-gates.md)
- [Subagents](references/subagents.md)

## Completion evidence

- The gate record of each phase, and the `check_gate.py` output.
- The work plan, and the `check_work_items.py` output with its waves.
- For each worker: its brief, its result with commands, and an
  in-scope diff check.
- Review findings with their dispositions, and the change requests
  with the gates they reopened.
- The final verification matrix, and what stays unavailable or not run.

## Stop and ask

- A gate cannot close without evidence that needs access or approval.
- A change request alters the scope the user accepted.
- The host cannot isolate parallel writers, and the work cannot be
  serialized within the time available.

[host]: references/subagents.md#host-capabilities
[brief]: references/subagents.md#work-item-brief
[results]: references/subagents.md#worker-result-contract
[waves]: references/subagents.md#parallel-waves-from-ownership
[worktrees]: references/subagents.md#worktree-isolation
[review]: references/subagents.md#independent-review
[diagnosis]: references/subagents.md#coordination-failure-diagnosis
[p1]: references/phases-and-gates.md#phase-1-requirements-baseline
[p2]: references/phases-and-gates.md#phase-2-design-baseline-with-ownership
[p3]: references/phases-and-gates.md#phase-3-implementation-by-work-item
[p4]: references/phases-and-gates.md#phase-4-integration-and-verification
[p5]: references/phases-and-gates.md#phase-5-release-preparation
[gates]: references/phases-and-gates.md#gate-decision-from-evidence
[change]: references/phases-and-gates.md#baseline-change-request
