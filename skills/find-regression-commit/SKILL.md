---
name: find-regression-commit
description: >-
  Find and verify the first Git commit that introduces a reproducible regression
  using an isolated worktree and a trustworthy bisect oracle. Excludes general
  debugging, lost-commit recovery, and history integration.
---

# Find Regression Commit

Define a deterministic good/bad oracle and known boundary commits. Read
[bisect workflow](references/bisect-workflow.md).

Run bisect in an isolated worktree. Treat unavailable dependencies or invalid
builds as untestable rather than bad. Save the bisect log, reproduce the
candidate and its parent, reset the bisect, and report ambiguity caused by
skips.
