# Commits

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

## Contents

- [Stage one hunk without a prompt](#stage-one-hunk-without-a-prompt)
- [Hooks that change the snapshot](#hooks-that-change-the-snapshot)
- [Fixups and autosquash](#fixups-and-autosquash)

## Stage one hunk without a prompt

Agents cannot drive `git add -p`. Write the hunk to a patch and apply it to the index only:

```sh
git diff -U0 app.txt > full.patch
awk '/^@@/{n++} n<2' full.patch > first.patch   # header plus first hunk
git apply --cached --unidiff-zero first.patch
git diff --cached app.txt   # first hunk staged
git diff app.txt            # the rest still unstaged
```

For a later hunk, change the `awk` condition to `n==1 || n==K`. Commit with a plain `git commit`,
not `git commit app.txt`, which would take the whole worktree file.

## Hooks that change the snapshot

A `pre-commit` hook (formatter, lefthook, husky) may edit and stage files, so the commit can differ
from the index you reviewed.

```sh
expected=$(git write-tree)
git commit -m "..."
test "$(git rev-parse 'HEAD^{tree}')" = "$expected" || git show --stat HEAD
```

On a mismatch, read `git show HEAD`, rerun the checks on the committed tree, and keep the hook's
edits only if they belong in this commit. If a hook fails, fix the cause; do not use `--no-verify`.

## Fixups and autosquash

To fix an earlier commit that is not pushed:

```sh
git commit --fixup=<sha>
git rebase -i --autosquash <sha>~1
```

Set `GIT_SEQUENCE_EDITOR=true` to accept the generated todo list without an editor. Create the
backup ref first. If the commit is already pushed, add the fixup as a normal follow-up commit
instead.
