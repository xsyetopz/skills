---
name: git-operations
description:
  Perform local Git commits, branching, integration, history inspection, or
  recovery while preserving unrelated work. Excludes hosted issues and pipeline
  implementation.
---

# Git Operations

Inspect HEAD, branch, worktrees, staged/unstaged changes, and any in-progress
operation. Select only paths or hunks belonging to the task.

Use Conventional Commits 1.0.0 for commit messages unless the user specifies
another format. Keep one coherent change per commit. Inspect the staged diff
before committing, then verify the resulting commit and worktree.

Read [state and recovery](references/state-and-recovery.md) for commit syntax,
restore/reset/revert, integration, conflicts, reflogs, bisect, and
force-with-lease.

Before rewriting history, create a recovery ref. Save dirty files separately:
refs protect commits only. Resolve conflicts from both sides' intended behavior.
Use the active operation's continue/abort commands.

A discard must identify the affected work. Bind an authorized force push to the
reviewed remote OID. Verify resulting refs and relevant project checks. Report
remaining conflicts or unrelated changes.
