---
name: commit-and-rewrite-git
description: >-
  Commits, stages exact hunks, and rewrites or recovers git history
  with amend, squash, rebase, reset, revert, reflog, stash, force-push, and bisect.
  Use when asked to commit, stage, undo, squash, rebase, recover lost commits,
  or find the commit that broke a test.
  Not for GitHub PRs or issues.
---

# Commit and Rewrite Git

Change repository state exactly as asked, without losing work or widening the request. The rules
below are the mistakes agents make with `git`.

## Rules

- Before any rewrite or discard (`rebase`, `reset --hard`, `commit --amend`, `filter-repo`,
  `clean -f`, `checkout -- .`, `stash drop`), create a backup ref of what you discard:
  `git branch backup/NAME HEAD` (for `stash drop`, `git branch backup/NAME 'stash@{N}'`), with a
  unique NAME such as date and task. A ref protects only commits, so commit or `git stash push -u`
  dirty files first. Without it, recovery depends on reflog archaeology.
- Do not run a destructive or outward-facing command (push, tag push, branch delete) the user did
  not name. Stop and ask the user before it; it changes shared state others can see. "Clean up"
  does not authorize `reset --hard`, and "commit this" authorizes no push or rewrite.
- Force-push only when the user asked for that push (a requested rebase does not include it), and
  only with an explicit lease: `git push --force-with-lease=refs/heads/BR:SHA origin BR`, where SHA
  is a value you reviewed. Never `--force`. A bare `--force-with-lease` uses the remote-tracking
  ref, which a background fetch can refresh, so the lease then protects nothing.
- Do not amend, rebase, or reset a commit that is already pushed unless the user authorized
  rewriting that branch. Add a `fixup!` commit or a `git revert` instead. Revert a merge with
  `-m 1`.
- Stage named paths, never `git add -A` or `git commit -a` in a tree that holds unrelated work. Read
  `git status --short` and `git diff --cached --stat` before each commit, because staged files from
  earlier work are committed too.
- `git commit PATH` and `--only` commit the path's whole worktree content and ignore what you
  staged. To commit a partial file, stage hunks first and run a plain `git commit`. Read
  [`references/commits.md`](references/commits.md) for scripted hunk staging.
- Do not pass `--no-verify` or change `core.hooksPath` to get past a failing hook. Fix the cause.
  When a hook can rewrite files, compare `git write-tree` before the commit with
  `git rev-parse 'HEAD^{tree}'` after it.
- In a rebase conflict `--ours` is the branch being rebased onto and `--theirs` is your commit being
  replayed, the reverse of a merge. Run `git diff --name-only --diff-filter=U` and read each side
  before choosing.
- Do not move or delete an existing tag or release tag. Report the conflict.
- Follow the repository's commit message, merge policy, and agent attribution rules (look in
  `AGENTS.md`, `CONTRIBUTING.md`, and `git log -10`). Do not invent a style.
- When the user wants commit messages linted, use
  [`assets/commitlint.config.mjs`](assets/commitlint.config.mjs) (Conventional Commits) and the
  `commit-msg` hook in [`assets/lefthook.yml`](assets/lefthook.yml). Add `@commitlint/cli`,
  `@commitlint/config-conventional`, and `lefthook` as dev dependencies with the repository's
  package manager, change the hook's `bun`/`bunx` to it, and run `lefthook install`. If a commitlint
  or lefthook config exists, ask whether to replace it or merge the hook in, and keep it until the
  user answers.
- Leave pull requests, issues, reviews, labels, and other `gh` work to
  `$triage-github-prs-and-issues`, and CI workflow files to `$write-ci-workflow`.

### Bisect

- Bisect in `git worktree add --detach ../REPO-wt BAD`, never in a tree holding the user's work. At
  the end run `git bisect reset` and remove the worktree.
- Run one oracle on both endpoints before searching: it exits 0 on the good commit and fails with
  the reported symptom on the bad one. Keep it at an absolute path outside the repository.
- `git bisect run` exit codes: 0 good, 1-127 except 125 bad, 125 skip, above 127 abort. A shell
  returns 127 for "command not found", which would be marked bad, so map statuses with
  `scripts/bisect_oracle.py`. Map build breaks and unrelated errors to skip, never bad.
- `git bisect start` and `git bisect reset` take no `-q`; `start -q` ignores both revisions.
- Never report one culprit from a bisect that ended with `only 'skip'ped commits left`; report the
  candidate set. Verify a culprit: its parent passes, it fails, and reverting it on the bad endpoint
  passes.

## Workflow

1. Read the state: `git status --short --branch`, `git diff --cached --stat`,
   `git log -5 --oneline`, and `git stash list`.
1. Make a backup ref when the next step rewrites history.
1. Run the narrowest command that does the job.
1. Read back: `git status` and `git show --stat HEAD`. Report refs and anything left behind such as
   stashes, backup branches, worktrees, or a bisect in progress.

## Scripts

Run these from the skill directory or by full path. On Windows, use `py -3` for `python3`.

- `python3 scripts/bisect_oracle.py [--bad-exit N]... [--skip-exit N]... [--timeout S] -- CMD ARGS`
  maps a test's statuses to bisect's contract (0 good, 1 bad, 125 skip, 128 abort) without a shell.
- Tests: `python3 -m unittest discover -s scripts`.

## References

- Read [`references/commits.md`](references/commits.md) when splitting one file across commits, when
  hooks run on commit, or when fixing up earlier unpublished commits.
- Read [`references/recovery.md`](references/recovery.md) when commits or files are lost, before a
  reset, revert, or rebase with conflicts, or when working in a second worktree.
- Read [`references/bisect.md`](references/bisect.md) before starting `git bisect`, when a search
  skips commits or hits flaky or performance tests, and before reporting a culprit.
