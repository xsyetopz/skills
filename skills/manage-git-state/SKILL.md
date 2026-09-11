---
name: manage-git-state
description: >-
  Use only when explicitly invoked by name. Create scoped Git commits, integrate
  branches, manage refs or tags, and recover or restore identified Git state
  while preserving unrelated work. Excludes hosted PR/MR management, repository
  settings, and regression bisection.
---

# Manage Git State

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Establish the requested state change and its authorization. Inspect HEAD,
branch/worktrees, index, worktree, and any in-progress operation. Distinguish
committed objects from staged blobs and unsaved file contents.

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
