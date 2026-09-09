# Git state transitions and recovery

Research: 2026-09-09; current Git 2.55-era manuals. Refresh for an unavailable
option or a different backend/version behavior.

## Establish three distinct states

Run `git status --short --branch`, `git diff`, `git diff --cached`,
`git log -5 --oneline`, and `git worktree list`. HEAD identifies a commit, the
index is the proposed next snapshot, and the worktree contains current files. A
branch backup protects commits, not dirty files. A detached HEAD can contain
useful commits; create a branch before losing their convenient reference.
[Status](https://git-scm.com/docs/git-status),
[worktrees](https://git-scm.com/docs/git-worktree).

Stage only intended paths or use `git add -p -- path`. Inspect
`git diff --cached` immediately before `git commit`; hooks can change files or
fail. Verify `git show --stat --oneline HEAD` and status afterward. Existing
staged changes must not enter the commit by accident. Reinspect the index after
a failed commit.

## Commit messages

Use Conventional Commits 1.0.0 unless the user specifies another format:

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footers]
```

Use `feat` for functionality and `fix` for bug fixes. Mark incompatible API
changes with `!` or a `BREAKING CHANGE:` footer. Other types, such as `docs`,
`refactor`, and `test`, do not imply a version increment by themselves. Name the
actual change in the description. Add rationale or migration details only when
needed. Keep release notes focused on user-visible changes instead of copying
the commit log. This message format does not require a hook or new tool.
[Conventional Commits 1.0.0][ref-1], checked 2026-09-09.

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

## Recover a lost commit or isolate a regression

Use `git reflog --date=iso` to find a candidate, inspect `git show CANDIDATE`,
then `git branch recovery/found CANDIDATE`. Prefer adding a ref over resetting
the current branch immediately. Reflogs are local, expire and do not record
arbitrary unsaved file contents. [Reflog](https://git-scm.com/docs/git-reflog).

In an isolated worktree, `git bisect start BAD GOOD`, then
`git bisect run /absolute/path/to/oracle`. The oracle returns 0 for good, 1–127
except 125 for bad, 125 for untestable, and other codes to abort. Missing
dependencies must not be mistaken for the product regression. Save
`git bisect log`, reproduce the candidate and parent, then `git bisect reset`.
Skips can leave several possible first bad commits.
[Bisect](https://git-scm.com/docs/git-bisect).

A shared-history correction usually uses a revert. If a force push is explicitly
authorized, bind `--force-with-lease=refs/heads/BRANCH:EXPECTED_OID` to the
reviewed remote value; plain `--force` discards the concurrency check.
[Push](https://git-scm.com/docs/git-push).

[ref-1]: https://www.conventionalcommits.org/en/v1.0.0/
