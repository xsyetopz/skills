---
name: manage-git-state
description: >-
  Create scoped Git commits, integrate branches, manage refs or tags, and
  recover or restore identified local Git state. Use when asked to commit
  changes, merge or rebase branches, create tags, recover commits, or
  manipulate the index/worktree; not for hosted PRs, repository settings, or
  regression bisection.
---

# Manage Git State

Apply this workflow when changing or recovering local Git state is the requested
work. Implicit activation selects guidance only; it does not authorize commits,
ref changes, history edits, or publication.

Establish the requested state change and its authorization. Inspect HEAD,
branch/worktrees, index, worktree, and any in-progress operation. Distinguish
committed objects from staged blobs and unsaved file contents.

- Read [mandatory local feedback](references/local-feedback.md) before code
  commits, commit-producing integrations, or pushes: enforce the repository's
  commit-message policy with generated hooks, require pre-commit/pre-push
  checks, and preserve hook ownership and the exact validated snapshot.
- Read [snapshots and refs](references/snapshots-and-refs.md) for scoped
  commits, partial staging, branch/tag identity, and remote ref updates.
- Read [integration and recovery](references/integration-and-recovery.md) for
  merge/rebase/cherry-pick, stash/worktree ownership, restore/reset/revert, and
  reflog recovery.

Preserve unrelated work and configured checks. A ref protects commits, not dirty
files. Before an authorized rewrite, retain the original committed and dirty
state separately. Prefer the narrow Git operation that produces the requested
result; do not turn an ordinary commit into branch restructuring or publication.

Verify the resulting commit/tree/ref and remaining staged/unstaged work. A
successful command alone does not prove the intended content was committed or
preserved. Report unresolved conflicts or unavailable validation; do not bypass
hooks, signing requirements, or failed checks.
