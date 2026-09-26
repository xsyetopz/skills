# History operations and recovery

Integrating, undoing, and recovering work. Scenarios are in
[`assets/examples/verify.sh`](../assets/examples/verify.sh) (git 2.55.0).

## Contents

- Recovery ref before a rewrite
- Stash with untracked files and index
- Merge policies
- Rebase and conflict sides
- Cherry-pick with provenance
- Revert, including merges
- Reset and restore transitions
- Reflog recovery
- Worktrees

## Recovery ref before a rewrite

**Definition.** A branch or tag created at the current commit before a
rebase, reset, or filter, which keeps the old history reachable by name.

**Use when.** Before any authorized history rewrite.

**Do not use when.** You need to protect uncommitted files. A ref protects
only commits; stash or commit dirty work separately.

**Example.**

```sh
git branch "recovery/before-rebase-$(date +%Y%m%d%H%M%S)" HEAD
```

**Cost removed.** Searching the reflog under pressure.

**Verify.**

1. `git rev-parse recovery/...` equals the old HEAD.

## Stash with untracked files and index

**Definition.** `git stash push -u -m MSG [-- PATH...]` saves staged,
unstaged, and untracked changes (ignored files need `-a`).
`git stash apply --index` restores the staged/unstaged split and keeps the
stash until you drop it ([git-stash][stash]).

**Use when.** Clearing the tree briefly for a rebase, pull, or checkout.

**Do not use when.** The work must survive for long; commit it on a
branch. Avoid `stash pop` until the restore is verified, because pop
drops the stash.

**Example.**

```sh
git stash push -u -m 'before integration'
git stash show -p --include-untracked 'stash@{0}'
# ... integrate ...
git stash apply --index
git stash drop   # only after verifying
```

**Cost removed.** Lost untracked files or a lost staged/unstaged split.

**Verify.**

1. `verify.sh` asserts staged, unstaged, and untracked states all return.

## Merge policies

**Definition.** `git merge --ff-only` succeeds only when the branch can
fast-forward and refuses otherwise; `--no-ff` always records a merge
commit ([git-merge][merge]).

**Use when.** Updating a local branch from upstream without creating
merges (`--ff-only`), or merging a feature where the project keeps merge
commits (`--no-ff`).

**Do not use when.** The project's policy is rebase-and-fast-forward;
follow it.

**Example.**

```sh
git merge --ff-only origin/main
git merge --no-ff -m 'merge topic' topic
```

**Cost removed.** Accidental merge commits and lost feature grouping.

**Verify.**

1. `verify.sh`: `--ff-only` fails on divergence; `--no-ff` produces a
   commit with two parents (`git rev-list --parents -n1 HEAD`).

## Rebase and conflict sides

**Definition.** `git rebase UPSTREAM` replays the current branch's commits
on top of `UPSTREAM`, creating new commit IDs. In a rebase conflict,
`--ours` is the upstream side being built on and `--theirs` is the commit
being replayed (your branch): the reverse of a merge
([git-rebase][rebase], [git-checkout][checkout]).

**Use when.** Updating an unpublished branch, or a published one when the
project's policy allows force-updates with a lease.

**Do not use when.** The branch is shared and nobody authorized rewriting
it.

**Example.**

```sh
git rebase main
git diff --name-only --diff-filter=U     # conflicted paths
git checkout --theirs app.txt            # keep the feature's version
git add app.txt && git rebase --continue
# or: git rebase --abort
```

**Cost removed.** The wrong side of a conflict kept.

**Verify.**

1. `verify.sh` asserts `--ours` yields the main branch's line and
   `--theirs` the feature's line, then aborts cleanly.

## Cherry-pick with provenance

**Definition.** `git cherry-pick -x COMMIT` applies a commit's change to
the current branch and appends `(cherry picked from commit <hash>)` to the
message ([git-cherry-pick][cherry-pick]).

**Use when.** Backporting a fix to a release branch.

**Do not use when.** Many related commits need to move; merge or rebase
the range to keep them together.

**Example.**

```sh
git switch release-1.x
git cherry-pick -x "$FIX"
```

**Cost removed.** Untraceable backports.

**Verify.**

1. `git log -1 --format=%B` contains the trailer (`verify.sh`).

## Revert, including merges

**Definition.** `git revert COMMIT` adds a commit that undoes another
commit's change without rewriting history. For a merge, `-m 1` keeps the
first parent as the mainline ([git-revert][revert]).

**Use when.** Undoing a published change.

**Do not use when.** The change is unpublished and a reset or fixup is
simpler and authorized.

**Example.**

```sh
git revert --no-edit "$COMMIT"
git revert --no-edit -m 1 "$MERGE"
```

To re-merge a branch after reverting its merge, revert the revert first;
Git considers the branch's commits already merged.

**Cost removed.** Force-pushes to undo shared history.

**Verify.**

1. `verify.sh` reverts a merge and asserts the branch's file is gone.

## Reset and restore transitions

**Definition.** What each command changes:

| Command | HEAD/branch | Index | Worktree |
| --- | --- | --- | --- |
| `git restore --staged -- F` | unchanged | F from HEAD | unchanged |
| `git restore -- F` | unchanged | unchanged | F from index |
| `git reset --soft C` | moves to C | unchanged | unchanged |
| `git reset --mixed C` | moves to C | from C | unchanged |
| `git reset --hard C` | moves to C | from C | from C (discards) |

**Use when.** Undoing staging or commits with the narrowest command.

**Do not use when.** You would run `reset --hard` or `restore` over
uncommitted work that is not saved elsewhere; both discard it.

**Example.**

```sh
git reset --soft HEAD~1     # uncommit, keep changes staged
git restore --staged app.txt
```

**Cost removed.** Work lost to `--hard` where `--soft` sufficed.

**Verify.**

1. `verify.sh` checks the index and worktree after each command.

## Reflog recovery

**Definition.** `git reflog` lists where HEAD and each branch pointed,
including commits no longer on any branch; `HEAD@{n}` names those
positions ([git-reflog][reflog]).

**Use when.** A reset, rebase, or amend lost commits.

**Do not use when.** The lost work was never committed; the reflog cannot
restore it. Look for stashes or editor backups.

**Example.**

```sh
git reflog -10
git branch rescue 'HEAD@{1}'
```

**Cost removed.** Redoing lost work by hand.

**Verify.**

1. `verify.sh` resets `--hard`, then restores the commit by reflog and
   compares hashes.

## Worktrees

**Definition.** `git worktree add [-b BRANCH] PATH [COMMIT]` creates another
checkout with its own index and HEAD that shares objects and refs. A
branch can be checked out in only one worktree at a time
([git-worktree][worktree]).

**Use when.** Investigating or building another commit without touching
the current checkout.

**Do not use when.** The worktree to remove has uncommitted changes:
`git worktree remove` refuses, and `--force` discards them.

**Example.**

```sh
git worktree add -b investigate ../repo-investigate HEAD
git -C ../repo-investigate status --short
git worktree remove ../repo-investigate
```

**Cost removed.** Stashing and switching branches back and forth.

**Verify.**

1. `verify.sh` commits in the worktree and asserts the main checkout is
   unchanged.

[stash]: https://git-scm.com/docs/git-stash
[merge]: https://git-scm.com/docs/git-merge
[rebase]: https://git-scm.com/docs/git-rebase
[checkout]: https://git-scm.com/docs/git-checkout
[cherry-pick]: https://git-scm.com/docs/git-cherry-pick
[revert]: https://git-scm.com/docs/git-revert
[reflog]: https://git-scm.com/docs/git-reflog
[worktree]: https://git-scm.com/docs/git-worktree
