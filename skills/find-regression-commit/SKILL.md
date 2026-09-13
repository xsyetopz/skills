---
name: find-regression-commit
description: >-
  Find and verify the first Git commit that introduced a reproducible failure
  with an isolated worktree and trustworthy bisect oracle. Not for general
  debugging or lost-commit recovery.
---

# Find Regression Commit

Define a deterministic good/bad oracle and known boundary commits. Read
[bisect workflow](references/bisect-workflow.md).

Honor existing [local feedback][local-feedback], but do not install hooks or
change historical candidates during bisection.

Run bisect in an isolated worktree. Distinguish unavailable prerequisites from
the target regression; a compiler failure can itself be the requested bad
behavior. Save the bisect log, reproduce the reported candidate and relevant
predecessor, reset the bisect, and report ambiguity caused by skips.

[local-feedback]: ../manage-git-state/references/local-feedback.md
