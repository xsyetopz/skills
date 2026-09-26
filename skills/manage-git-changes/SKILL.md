---
name: manage-git-changes
description: >-
  Performs local Git operations without losing work: exact staging, commits
  and fixups, rebase and conflicts, cherry-pick, revert, reset, reflog
  recovery, worktrees, force-with-lease. Use when changing Git history or
  state. Not for hosted pull requests.
---

# Manage Git Changes

Change Git state exactly as requested and nothing more. Each commit holds
the intended snapshot, unrelated staged, unstaged, and untracked work
survives, history is rewritten only when authorized, and HEAD, the index,
and the worktree are checked after every operation.

## Workflow

1. Read the state: `git status --short --branch`, `git diff --cached
   --stat`, `git diff --stat`, `git log -5 --oneline`, `git worktree
   list`, `git stash list` ([three states][states]).
1. Confirm that the user authorized this operation (commit, rewrite,
   push, tag). "Commit the changes" does not authorize a push or a
   rewrite.
1. Protect work before risky operations: a recovery branch for rewrites,
   `stash push -u` or a commit for dirty files
   ([recovery ref][recovery]).
1. Find the repository's hooks, commit message policy, and merge or
   rebase policy.
1. Perform the operation with the narrowest command from the cards.
1. Verify: status and diffs again, `git show --stat HEAD`,
   `write-tree` versus `HEAD^{tree}` where hooks run, and the checks for
   the committed slice.
1. Report the resulting refs and state, and anything left (stashes,
   recovery branches, worktrees).

## Route the task to a card

| Task | Card |
| --- | --- |
| Commit some of the current changes | [Stage exact paths](references/staging-and-commits.md#stage-exact-paths), [one hunk](references/staging-and-commits.md#stage-one-hunk-without-a-prompt) |
| File has staged and unstaged edits | [commit --only trap](references/staging-and-commits.md#the-commit---only-trap) |
| Hooks run on commit | [Existing hooks](references/staging-and-commits.md#existing-hooks), [hooks change snapshot](references/staging-and-commits.md#hooks-that-change-the-snapshot), [write-tree](references/staging-and-commits.md#snapshot-identity-with-write-tree) |
| Several changes in the tree | [Commit slices](references/staging-and-commits.md#commit-slices-by-behavior) |
| Writing the message | [Message policy](references/staging-and-commits.md#commit-message-policy) |
| Fix an earlier unpublished commit | [Fixup and autosquash](references/staging-and-commits.md#fixup-commits-and-autosquash), [amend](references/staging-and-commits.md#amend) |
| Clear the tree temporarily | [Stash](references/history-and-recovery.md#stash-with-untracked-files-and-index) |
| Bring in another branch | [Merge policies](references/history-and-recovery.md#merge-policies), [rebase](references/history-and-recovery.md#rebase-and-conflict-sides) |
| Conflict during rebase | [Conflict sides](references/history-and-recovery.md#rebase-and-conflict-sides) |
| Backport a fix | [Cherry-pick -x](references/history-and-recovery.md#cherry-pick-with-provenance) |
| Undo a published change or merge | [Revert](references/history-and-recovery.md#revert-including-merges) |
| Unstage, uncommit, discard | [Reset and restore](references/history-and-recovery.md#reset-and-restore-transitions) |
| Commits lost after reset or rebase | [Reflog](references/history-and-recovery.md#reflog-recovery) |
| Work on another commit in parallel | [Worktrees](references/history-and-recovery.md#worktrees) |
| Tag a release | [Annotated tags](references/tags-and-publishing.md#annotated-release-tags), [publishing tags](references/tags-and-publishing.md#publishing-tags) |
| Push, or push a rewritten branch | [Pushing](references/tags-and-publishing.md#pushing-a-branch), [force-with-lease](references/tags-and-publishing.md#force-with-lease) |

## Rules

- Never discard uncommitted work (`reset --hard`, `restore`, `checkout --
  .`, `clean -f`, `stash drop`) without the user's go-ahead for that
  action.
- Stage named paths; never `git add -A` in a tree with unrelated changes.
- Do not bypass hooks (`--no-verify`) or change `core.hooksPath`.
- Rewrite (amend, rebase, reset of pushed commits) only when authorized.
  Publish a rewrite only with `--force-with-lease=REF:EXPECTED`; a bare
  `--force-with-lease` compares against the remote-tracking ref, which a
  background fetch can update.
- During a rebase, `--ours` is the upstream side and `--theirs` is the
  commit being replayed.
- `git commit PATH` commits the path's worktree content, not its staged
  hunks.
- Do not move an existing release tag; report the conflict.

## Bundled tools

- `assets/examples/verify.sh`: one scenario per card operation, in
  repositories under a temporary directory with isolated Git config.
- `scripts/test_commit_snapshots.py`: tests for index preservation and
  snapshot identity with partial staging and hooks.

## References

- [Staging and commits](references/staging-and-commits.md): three states,
  exact paths, hunk staging, the `--only` trap, write-tree, hooks, slices,
  message policy, fixups, amend.
- [History and recovery](references/history-and-recovery.md): recovery
  refs, stash, merge, rebase sides, cherry-pick, revert, reset/restore
  table, reflog, worktrees.
- [Tags and publishing](references/tags-and-publishing.md): annotated
  tags, pushes, force-with-lease, tag publication.

## Completion evidence

The report lists the operations run, the resulting `git log --oneline`
for affected refs, `git status --short` afterwards, each commit's
`--stat` and the checks run on it, and any stash, recovery branch,
worktree, or unpushed commit left behind.

[states]: references/staging-and-commits.md#inspect-the-three-states
[recovery]: references/history-and-recovery.md#recovery-ref-before-a-rewrite
