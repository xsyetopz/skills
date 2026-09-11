---
name: find-regression-commit
description: >-
  Use only when explicitly invoked by name. Find and verify the first Git commit
  that introduces a reproducible regression using an isolated worktree and a
  trustworthy bisect oracle. Excludes general debugging, lost-commit recovery,
  and history integration.
---

# Find Regression Commit

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Define a deterministic good/bad oracle and known boundary commits. Read
[bisect workflow](references/bisect-workflow.md).

Run bisect in an isolated worktree. Distinguish unavailable prerequisites from
the target regression; a compiler failure can itself be the requested bad
behavior. Save the bisect log, reproduce the reported candidate and relevant
predecessor, reset the bisect, and report ambiguity caused by skips.
