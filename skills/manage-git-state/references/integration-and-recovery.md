# Integration and recovery

## Preserve work before integration

Create a named recovery ref, such as `git branch recovery/before-rebase HEAD`,
before an authorized rewrite. Preserve dirty files separately with a reviewed
copy/patch or `git stash push -u -m 'before integration' -- paths`. `-u`
includes untracked files; ignored files require a separate deliberate choice.
Inspect `git stash show -p --include-untracked 'stash@{0}'`. Prefer
`stash apply --index` when restoring staged state matters, retaining the stash
until the result is verified. Conflicts can prevent index restoration.
[Stash](https://git-scm.com/docs/git-stash).

A linked worktree (`git worktree add -b investigate ../repo-investigate HEAD`)
gives a separate checkout/index but shares repository objects and refs. Do not
try to check out a branch already owned by another worktree or delete a dirty
worktree. Remove it with `git worktree remove` once its work is preserved.

## Merge, rebase and cherry-pick

A merge preserves both parent histories; `--ff-only` refuses a merge commit when
fast-forward is impossible. Rebase reapplies commits onto a new base, changing
IDs; use it according to the branch's publication policy. Cherry-pick reapplies
selected changes and can conflict even when their original commit built
successfully. [Merge](https://git-scm.com/docs/git-merge),
[rebase](https://git-scm.com/docs/git-rebase),
[cherry-pick](https://git-scm.com/docs/git-cherry-pick).

When stopped, inspect status and `git diff --name-only --diff-filter=U`. Read
both sides and the base; resolve intended behavior, stage resolved paths, run
the affected checks, then use the owning operation's `--continue`. Use its
`--abort` to return toward pre-operation state; this is not a backup for dirty
work. `rebase --skip` drops a commit's effect and needs evidence that it is
redundant. During rebase, “ours” denotes the rebased upstream side; do not
equate it with the user's original feature branch.

## Select the narrow transition

- **`git restore --staged -- file`** HEAD/ref: unchanged Index: restore file
  from HEAD Worktree: unchanged

- **`git restore -- file`** HEAD/ref: unchanged Index: unchanged Worktree:
  overwrite file from index

- **`git reset --soft COMMIT`** HEAD/ref: move current branch/HEAD Index:
  unchanged Worktree: unchanged

- **`git reset --mixed COMMIT`** HEAD/ref: move Index: match commit Worktree:
  unchanged

- **`git reset --hard COMMIT`** HEAD/ref: move Index: match commit Worktree:
  overwrite tracked state; can remove obstructing untracked files

- **`git revert COMMIT`** HEAD/ref: create inverse commit Index: participates in
  operation Worktree: apply inverse change

`restore` without `--staged` discards unstaged content for the selected paths.
Use `reset --hard` only to discard identified content after saving required
work. For an unborn branch, HEAD-based restore may be unavailable; inspect
before choosing an index-only removal.
[Restore](https://git-scm.com/docs/git-restore),
[reset](https://git-scm.com/docs/git-reset),
[revert](https://git-scm.com/docs/git-revert).

## Recover a lost commit

Inspect local reflogs for the candidate and read its tree/change before adding a
recovery branch at that object. Adding a ref preserves the object without moving
the current branch or replacing dirty files. Reflogs are local and expire; they
do not preserve arbitrary unsaved file contents. Confirm the recovered artifact,
not just that a branch was created. See
[reflog](https://git-scm.com/docs/git-reflog).

A shared-history correction usually uses a new revert commit instead of
rewriting published history. Reverting a merge requires choosing a mainline and
understanding later merge behavior; do not guess a parent solely from its
number. Consult the [revert contract](https://git-scm.com/docs/git-revert).
