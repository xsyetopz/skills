---
name: manage-git-changes
description: >-
  Use for authorized Git staging, commits, branches, merges, rebases,
  cherry-picks, reverts, worktrees, and recovery. Preserve unrelated
  working-tree and index changes. Not for routine source edits or automatically
  committing completed work.
---

# Manage Git Changes

Perform the requested Git state transition while preserving unrelated files,
staged content, references, history, configuration, and remote state. Inspect
the actual repository state before and after every potentially destructive or
history-changing operation.

## Operating contract

- Git tool availability does not authorize a commit, reset, rebase, force push,
  deletion, or remote write.
- Distinguish HEAD, index, working tree, untracked files, branches/tags,
  worktrees, remotes, and submodules. Never treat “clean” as a universal
  prerequisite.
- Preserve pre-existing staged and unstaged changes, including mixed changes to
  the same file. Use path- and patch-scoped operations.
- Prefer reversible operations and create recovery evidence before destructive
  history changes.
- Remote operations, force updates, tags, and published-history rewrites require
  explicit authority and branch/ruleset awareness.

## Git-state mutation contract

- Treat the user goal, scope, approval boundary, and required evidence as
  controlling. This skill narrows how to produce a local Git operation; it MUST
  NOT broaden authority or override repository instructions.
- For GPT-5.6 and GPT-6, provide HEAD, index, worktree, refs, remotes, unrelated
  changes, and requested history operation, hard constraints, available tools,
  and the finish condition once. Remove repeated directions and examples unless
  a recorded evaluation shows that they prevent a real failure.
- Infer routine, reversible steps from inspected evidence. Ask only when an
  unresolved choice changes an external contract. Stop before an external write,
  destructive action, credential use, or material scope expansion that the user
  did not authorize.
- Load a linked reference only when its subject affects the current decision.
  Use scripts for deterministic mechanics; use model judgment for semantic
  decisions. Inspect tool output before relying on it.
- Validate at the boundary of the claim with before/after status, diffs,
  reflogs, and commit graph checks. Report commands, observed results, and gaps.
  A parser, build, or single green test proves only the property that it can
  discriminate.
- Use **MUST** only for an absolute safety or interoperability requirement,
  **SHOULD** for a default with valid exceptions, and **MAY** for an option.
  Write short active sentences and use one stable term for each concept. This
  style is STE-inspired; it is not a claim of formal ASD-STE100 conformance.

## Workflow

```mermaid
stateDiagram-v2
    [*] --> WorkingTree
    WorkingTree --> Index: git add / restore --staged inverse
    Index --> Commit: git commit
    Commit --> BranchRef: branch points to commit
    BranchRef --> RemoteRef: authorized push
    Commit --> WorkingTree: checkout/restore content
    BranchRef --> Reflog: ref movement recorded locally
    Reflog --> BranchRef: recovery when object remains
```

## Procedure

1. Inspect repository root, status with porcelain details, current branch/HEAD,
   index versus worktree diff, untracked/ignored files as relevant, worktrees,
   in-progress operations, remotes, upstream, and applicable hooks/rules.
1. Translate the request into an exact state transition and mutation boundary.
   Identify unrelated state to preserve and whether the action changes local
   content, index, references, history, or remote state.
1. For staging/commit, select exact paths/hunks and inspect the staged snapshot
   (`git diff --cached`). Do not stage generated, secret, lockfile, or unrelated
   changes merely because they are present.
1. For merge/rebase/cherry-pick/revert, establish bases and intended history
   semantics. Preserve a recovery reference or record current refs where risk
   warrants it. Resolve conflicts from the actual contract, not by choosing
   ours/theirs wholesale.
1. For reset/restore/clean/drop/force operations, confirm explicit necessity and
   authority; use the narrowest reversible alternative. Never delete untracked
   data without identifying it and authorization.
1. Run repository checks required for the requested change and inspect final
   diffs/status/history. Hooks may modify files; re-inspect rather than assuming
   the intended snapshot was committed.
1. For remote operations, verify destination, refspec, lease/current remote
   state, protections, and result. Report exact commits/refs changed and
   preserved unrelated state.

## Choose the Git-state reference

| Situation | Read or use |
| --- | --- |
| Staging, committing, restore/reset, hooks, and snapshots | [Snapshots and refs](references/snapshots-and-refs.md) |
| Merge, rebase, cherry-pick, revert, push, and recovery | [Integration and recovery](references/integration-and-recovery.md) |
| Interpreting local Git feedback safely | [Local feedback](references/local-feedback.md) |
| Choosing the least destructive operation | [Operational decisions](references/local-git-state-operational-decisions.md) |
| Using complete mixed-index, conflict, worktree, and recovery examples | [Worked scenarios](references/local-git-state-worked-scenarios.md) |
| Proving state transitions and preservation | [Verification and claim evidence](references/local-git-state-verification-and-claim-evidence.md) |
| Avoiding resets, force updates, and retry mistakes | [Failure patterns and recovery](references/local-git-state-failure-patterns-and-recovery.md) |
| Testing staged-snapshot assumptions | [Commit snapshot tests](scripts/test_commit_snapshots.py) |
| Checking official Git semantics | [Standards, APIs, and authorities](references/local-git-state-standards-apis-and-authorities.md) |

## Git operation references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Concepts, contracts, and invariants](references/local-git-state-concepts-contracts-and-invariants.md) | Use when distinguishing the requested local Git operation from observed repository state. |
| [Enterprise operation and governance](references/local-git-state-organizational-controls-and-scale.md) | Use when the local Git operation crosses ownership, data-handling, release, or audit boundaries. |
| [Bundled resource map](references/local-git-state-bundled-resource-map.md) | Use when locating bundled resources for the local Git operation. |

## Behavioral evaluation

Run [the maintained Agent Skills evaluations](evals/evals.json) in clean
target-client contexts. Compare this revision with a no-skill or prior-skill
baseline. Review commands, diffs, and artifacts; do not grade prose alone. The
checked-in cases are test inputs, not claimed results.

## Bundled executable helpers

- `scripts/test_commit_snapshots.py`

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- No output template is mandatory. Preserve the repository's established format.

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Exact authorized Git transition and pre-operation state.
- Changed local/remote refs, commits, index/worktree paths, and conflict
  resolutions.
- Final staged/unstaged/untracked status and relevant history.
- Checks/hooks actually executed and post-hook diff.
- Recovery reference/steps where material.
- Explicit preservation of unrelated state.

## Stop or escalate

- The requested destructive/remote effect is not explicit or conflicts with
  protections.
- An in-progress Git operation or unexpected repository state changes the
  requested transition.
- Unrelated user changes cannot be preserved safely with the proposed command.
- Remote state changed and a force/retry would risk overwriting another actor.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
