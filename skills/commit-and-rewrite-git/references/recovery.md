# Recovery and Undo

## Contents

- [Reflog Recovery](#reflog-recovery)
- [Reset and Restore](#reset-and-restore)
- [Revert, Including Merges](#revert-including-merges)
- [Stash](#stash)
- [Rebase Conflicts](#rebase-conflicts)
- [Worktrees](#worktrees)

## Reflog Recovery

The reflog restores committed work only. Uncommitted edits that were discarded are gone; look for
stashes or editor backups.

```sh
git reflog -15
git branch rescue 'HEAD@{2}'    # name the lost commit before anything else
git show --stat rescue
```

Create the branch first, then decide what to merge or cherry-pick from it. Entries expire (90 days
by default, 30 for unreachable).

## Reset and Restore

Pick the narrowest row:

| Command | HEAD | Index | Worktree |
| --- | --- | --- | --- |
| `git restore --staged -- F` | same | F from HEAD | same |
| `git restore -- F` | same | same | F from index (discards) |
| `git reset --soft C` | to C | same | same |
| `git reset --mixed C` | to C | from C | same |
| `git reset --hard C` | to C | from C | from C (discards) |

To uncommit and keep the changes staged, use `git reset --soft HEAD~1`.

## Revert, Including Merges

`git revert --no-edit SHA` undoes a published commit without rewriting history. For a merge commit
add `-m 1` (keep the first parent). To merge the same branch again after reverting its merge, revert
the revert first; Git treats the branch's commits as already merged.

## Stash

```sh
git stash push -u -m "before rebase"
git stash show -p --include-untracked 'stash@{0}'
git stash apply --index      # restores the staged and unstaged split
git stash drop               # only after checking the result
```

Use `apply`, not `pop`: `pop` drops the stash even when the apply was partial or conflicted. Plain
`stash` skips untracked files, and ignored files need `-a`. Anything meant to live longer belongs on
a branch.

## Rebase Conflicts

```sh
git diff --name-only --diff-filter=U
git checkout --theirs app.txt   # your commit's version during a rebase
git add app.txt && git rebase --continue
git rebase --abort              # back to the pre-rebase state
```

During a rebase, `--ours` is the upstream you are replaying onto. After the rebase, compare with the
backup ref: `git range-diff backup/NAME...HEAD` or `git diff backup/NAME HEAD`. Publish only with an
explicit lease (see `SKILL.md`). `git merge --ff-only origin/main` updates a local branch without
creating a merge commit and fails on divergence; use `--no-ff` only when the project keeps merge
commits.

## Worktrees

To inspect or fix another commit without touching the dirty tree:

```sh
git worktree add ../hotfix origin/release-1.x
git worktree remove ../hotfix
```

A branch can be checked out in only one worktree. Remove the worktree when done and report any left
behind.
