---
name: manage-git-state
description: >-
  Create scoped commits, integrate branches, manage refs or tags, and recover or
  restore local Git state. Not for hosted pull requests or regression bisection.
---

# Manage Git State

Establish the requested state change and its authorization. Inspect HEAD,
branch/worktrees, index, worktree, and any in-progress operation. Distinguish
committed objects from staged blobs and unsaved file contents.

Before commit-producing work, choose the intended slices and message policy.
“Stage and commit current changes” authorizes the content, not one omnibus
commit. Unless explicitly asked for one commit, group independently revertible
behavior with its tests and necessary documentation; keep inseparable changes
together and order dependent slices so each resulting snapshot is valid.
Do not reshape existing history to apply this rule.

Honor explicit repository message policy. If none exists, use Conventional
Commits (`type(scope): summary`, with optional scope and the appropriate
breaking-change marker). Resolve conflicting policies before committing; do not
install a validator merely to enforce this fallback. Read the policy-selection
details in [snapshots and refs](references/snapshots-and-refs.md) before
creating or rewording commits.

- Read [local feedback](references/local-feedback.md) before code commits,
  commit-producing integrations, or pushes. Honor existing hooks and repository
  policy; do not install a hook manager unless that work is requested.
- Read [snapshots and refs](references/snapshots-and-refs.md) for scoped
  commits, partial staging, branch/tag identity, and remote ref updates.
- Read [integration and recovery](references/integration-and-recovery.md) for
  merge/rebase/cherry-pick, stash/worktree ownership, restore/reset/revert, and
  reflog recovery.

Preserve unrelated work and configured checks. A ref protects commits, not dirty
files. Before an authorized rewrite, retain the original committed and dirty
state separately. Prefer the narrow Git operation that produces the requested
result; do not turn an ordinary commit into branch restructuring or publication.

Verify each intended staged snapshot, its relevant checks, the resulting
commit/tree/ref, and preserved remaining work. Passing hooks or a clean worktree
does not prove correct slicing. Report unresolved conflicts or unavailable
validation; do not bypass hooks, signing requirements, or failed checks.
