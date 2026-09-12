---
name: find-regression-commit
description: >-
  Find and verify the first Git commit that introduced a reproducible
  failure using an isolated worktree and a trustworthy bisect oracle. Use
  when asked which commit caused a regression or to run git bisect; not for
  general debugging, lost-commit recovery, or branch integration.
---

# Find Regression Commit

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Define a deterministic good/bad oracle and known boundary commits. Read
[bisect workflow](references/bisect-workflow.md).

Apply [local feedback][local-feedback] as a read-only setup inspection; do not
install hooks or change historical candidates during bisection.

Run bisect in an isolated worktree. Distinguish unavailable prerequisites from
the target regression; a compiler failure can itself be the requested bad
behavior. Save the bisect log, reproduce the reported candidate and relevant
predecessor, reset the bisect, and report ambiguity caused by skips.

[local-feedback]: ../manage-git-state/references/local-feedback.md
