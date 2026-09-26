# Staging and commits

Building exactly the intended snapshot and commit. The scenarios are in
[`assets/examples/verify.sh`](../assets/examples/verify.sh) (16 checks,
measured with git 2.55.0 in disposable repositories);
`scripts/test_commit_snapshots.py` covers index preservation.

## Contents

- Inspect the three states
- Stage exact paths
- Stage one hunk without a prompt
- The commit --only trap
- Snapshot identity with write-tree
- Existing hooks
- Hooks that change the snapshot
- Commit slices by behavior
- Commit message policy
- Fixup commits and autosquash
- Amend

## Inspect the three states

**Definition.** HEAD is the last commit, the index is the proposed next
snapshot, and the worktree holds the current files. `git status --short`
shows two columns (index, worktree), `git diff --cached` shows index
versus HEAD, and `git diff` shows worktree versus index
([git-status][status], [git-diff][diff]).

**Use when.** Before and after every staging, commit, or history operation.

**Do not use when.** No exception. Changes staged by earlier work enter
the next commit unless you see and handle them.

**Example.**

```sh
git status --short --branch
git diff --cached --stat
git diff --stat
git log -5 --oneline
git worktree list
```

In `git status --short`, `M` in column 1 is staged, `M` in column 2 is
unstaged, and `??` is untracked.

**Cost removed.** Commits that carry unintended staged changes.

**Verify.**

1. `verify.sh` stages one file, edits another, adds an untracked file, and
   asserts the three porcelain lines for `README.md` (staged), `app.txt`
   (unstaged), and `untracked.txt`.

## Stage exact paths

**Definition.** `git add -- PATH...` stages the named paths; `git add -A`
and `git add .` stage everything, including files you did not mean to
commit.

**Use when.** Staging any change: name its paths.

**Do not use when.** No exception. Never use `-A` in a tree with unrelated
changes, build output, or secrets.

**Example.**

```sh
git add -- src/parser.py tests/test_parser.py
git diff --cached --stat   # only those two files
```

**Cost removed.** Secrets, generated files, and unrelated edits in
commits.

**Verify.**

1. `git diff --cached --name-only` lists exactly the intended paths.
1. `git diff --cached | rg -i 'secret|password|token|BEGIN .*PRIVATE KEY'`
   finds nothing.

## Stage one hunk without a prompt

**Definition.** `git add -p` stages hunks interactively. The scripted,
reviewable equivalent writes the hunk to a patch and applies it to the
index alone with `git apply --cached` ([git-apply][apply]).

**Use when.** One file holds two independent changes for different
commits, and the agent cannot drive an interactive prompt.

**Do not use when.** The whole file belongs to one commit.

**Example.**

```sh
git diff -U0 app.txt > full.patch
awk '/^@@/{n++} n<2' full.patch > first.patch   # header + first hunk
git apply --cached --unidiff-zero first.patch
git diff --cached app.txt   # first hunk staged
git diff app.txt            # second hunk still unstaged
```

**Cost removed.** Unrelated changes mixed in one commit.

**Verify.**

1. `verify.sh` asserts line 1 is staged and line 5 is not.

## The commit --only trap

**Definition.** `git commit --only -- PATH` (also `git commit PATH`)
commits the path's current **worktree** content, ignoring what you staged
for it, and leaves other staged paths out ([git-commit][commit]).

**Use when.** You intend to commit a whole file as it is on disk.

**Do not use when.** The file is partially staged: the unstaged hunk goes
into the commit.

**Example.** Measured: after staging only the first hunk of `app.txt`,
`git commit --only -m msg -- app.txt` committed both hunks. Commit the
staged snapshot with plain `git commit -m msg` instead.

From `assets/examples/verify.sh`, run right after staging only the line 1
hunk (as in the previous card), with line 5 changed but unstaged:

```sh
# 3. commit --only records the path's worktree content, not staged hunks.
git commit -q --only -m 'only' -- app.txt
[ "$(git show HEAD:app.txt | sed -n 5p)" = 'line 5 CHANGED' ] ||
    fail commit-only 'expected the unstaged hunk to be committed'
pass 'commit --only -- path committed the unstaged hunk as well'
```

**Cost removed.** Unreviewed hunks entering a commit.

**Verify.**

1. `verify.sh` shows that the committed file contains the unstaged hunk.
1. After any commit, `git show --stat HEAD` and `git diff HEAD~1 --
   PATH` match what you reviewed.

## Snapshot identity with write-tree

**Definition.** `git write-tree` prints the tree ID of the current index.
If the commit recorded exactly that index, `git rev-parse HEAD^{tree}`
prints the same ID afterwards ([git-write-tree][write-tree]).

**Use when.** Exact snapshot identity matters: hooks may run, or the
reviewed index must be what gets committed.

**Do not use when.** No hook or tool can modify the index during commit.

**Example.**

```sh
expected=$(git write-tree)
git commit -m 'feat: add parser'
[ "$(git rev-parse 'HEAD^{tree}')" = "$expected" ] || echo 'tree changed'
```

**Cost removed.** Commits that differ from what was reviewed.

**Verify.**

1. `verify.sh` asserts equality for a plain commit.

## Existing hooks

**Definition.** Git runs hooks from `core.hooksPath` (default
`.git/hooks`); hook managers (lefthook, pre-commit, husky) install them.
Hooks are part of the repository's contract ([githooks][githooks]).

**Use when.** Before any commit or push, to find what will run.

**Do not use when.** You would bypass a failure with `--no-verify`,
install or replace hooks, or reset `core.hooksPath`, unless the user asked
for hook work.

**Example.**

```sh
git config --get core.hooksPath
ls "$(git rev-parse --git-path hooks)"
fd -H -d 1 'lefthook.yml|.pre-commit-config.yaml|.husky' .
```

**Cost removed.** Commits that CI rejects, and checks silently skipped.

**Verify.**

1. After a hook failure, `git log -1` shows no new commit and
   `git status` shows the index unchanged. Fix the cause and commit
   again.

## Hooks that change the snapshot

**Definition.** A `pre-commit` hook may edit and stage files (formatters),
so the committed tree can differ from the index you reviewed.

**Use when.** The repository has hooks (`core.hooksPath`, lefthook,
pre-commit, husky).

**Do not use when.** You would bypass a failing hook with `--no-verify`;
fix the cause instead.

**Example.** In `verify.sh`, a hook appends to `README.md` and stages it,
so `HEAD^{tree}` differs from the pre-commit `write-tree` value. Review
`git show HEAD` and rerun the checks on the committed tree. From
`assets/examples/verify.sh`:

```sh
# 5. A hook that edits the index changes the committed tree.
mkdir -p "$WORK/hooks"
cat >"$WORK/hooks/pre-commit" <<'EOF'
#!/bin/sh
echo 'added by hook' >>README.md
git add README.md
EOF
chmod +x "$WORK/hooks/pre-commit"
echo 'second' >>app.txt
git add app.txt
expected=$(git write-tree)
git -c core.hooksPath="$WORK/hooks" commit -q -m 'with hook'
[ "$(git rev-parse 'HEAD^{tree}')" != "$expected" ] ||
    fail hook-tree 'expected the hook to change the tree'
pass 'pre-commit hook changed the committed tree; write-tree detects it'
```

**Cost removed.** Unreviewed hook edits shipped silently.

**Verify.**

1. Compare `write-tree` before with `HEAD^{tree}` after every commit in a
   hooked repository; on mismatch, inspect `git show HEAD`.

## Commit slices by behavior

**Definition.** Each new commit holds one independently understandable,
revertible behavior with its tests and docs. Boundaries follow behavior,
not file names or diff size.

**Use when.** Committing a worktree with several changes, unless the
user asked for one commit.

**Do not use when.** Splitting would leave a commit that does not build or
pass its tests; keep dependent changes together.

**Example.**

```text
fix(parser): reject empty keys          src/parser.py, tests/test_parser.py
docs: document the keys option          docs/options.md
```

For each slice: stage it, review `git diff --cached`, run the checks that
cover it, and commit.

**Cost removed.** Reverting one change forces reverting another.

**Verify.**

1. For each commit, `git show --stat` lists only its slice, and its checks
   pass on that commit (`git stash -u`, test, `git stash pop`, or a linked
   worktree at that commit).

## Commit message policy

**Definition.** A repository's message rules come from its contributor
docs, commit linter config (for example `commitlint.config.*`), hooks,
and CI. Without a policy, default to
[Conventional Commits 1.0.0][cc]: `type(scope): summary`, `feat`/`fix`
and other types, and `!` or a `BREAKING CHANGE:` footer for incompatible
changes.

**Use when.** Writing or rewording any commit message.

**Do not use when.** You would imitate recent history against an explicit
policy, or install a linter just to write a message.

**Example.**

```sh
fd -H -d 2 'commitlint|\.czrc|lefthook|pre-commit-config' .
bunx commitlint --from HEAD~1 --to HEAD   # when commitlint is configured
```

```text
fix(bisect): abort instead of marking bad on missing command

A missing test command exited 127, which git bisect run treats as bad.
```

**Cost removed.** Pushes and CI runs rejected by message rules.

**Verify.**

1. The repository's message linter passes on the new commits.

## Fixup commits and autosquash

**Definition.** `git commit --fixup=COMMIT` creates a commit titled
`fixup! <subject>`; `git rebase -i --autosquash BASE` moves it and folds it
into its target. `GIT_SEQUENCE_EDITOR=true` accepts the generated todo
list non-interactively ([git-rebase][rebase]).

**Use when.** Correcting an unpublished commit in a series and keeping the
series reviewable.

**Do not use when.** The target commit is on a shared branch and nobody
authorized rewriting it.

**Example.**

```sh
git commit --fixup "$TARGET"
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash "$TARGET~1"
```

**Cost removed.** Separate "fix typo" commits in history.

**Verify.**

1. `verify.sh` asserts the subjects after the rebase and that the target
   commit contains the fix.

## Amend

**Definition.** `git commit --amend` replaces HEAD with a new commit that
records the current index and either a new message or the same one
(`--no-edit`). The old commit stays reachable through the reflog.

**Use when.** The last commit is unpublished and the user asked to change
it.

**Do not use when.** The commit is pushed to a shared branch, or a hook
failed: the commit did not happen, so amending would modify the previous
one.

**Example.**

```sh
git add -- forgotten_test.py
git commit --amend --no-edit
```

**Cost removed.** An extra commit for a forgotten file.

**Verify.**

1. `git show --stat HEAD` includes the file; `git reflog -2` shows the
   amended commit.

[githooks]: https://git-scm.com/docs/githooks
[status]: https://git-scm.com/docs/git-status
[diff]: https://git-scm.com/docs/git-diff
[apply]: https://git-scm.com/docs/git-apply
[commit]: https://git-scm.com/docs/git-commit
[write-tree]: https://git-scm.com/docs/git-write-tree
[rebase]: https://git-scm.com/docs/git-rebase
[cc]: https://www.conventionalcommits.org/en/v1.0.0/
