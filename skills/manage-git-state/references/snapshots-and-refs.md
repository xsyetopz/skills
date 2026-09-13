# Snapshots, commits, and refs

Research: 2026-09-11; Git 2.55.0 manuals and installed executable.

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
fail. Stop if the staged content exposes credentials, private keys,
token-bearing configuration, or unrelated generated artifacts. Do not bypass a
failing hook. Verify `git show --stat --oneline HEAD` and status afterward.
Existing staged changes must not enter the commit by accident. Reinspect the
index after a failed commit.

## Commit messages

Unless the user explicitly requests one commit, divide future commits by
independently understandable behavior rather than file count or diff size. Keep
an implementation with its relevant tests and necessary documentation. Run the
relevant checks for each commit so every slice is independently valid and can be
reverted without invalidating an unrelated slice. Apply this policy only to new
commits; do not rewrite existing history to reshape earlier work.

Before composing a message or running an operation that creates or rewords a
commit, determine the repository's configured message policy. Inspect its
contributor documentation, message-linter configuration, hook-manager
configuration, and equivalent CI gate. Use recent reachable history only as
supporting evidence, not as a substitute for an explicit policy. If these
sources conflict, stop and report the conflict instead of choosing a style.

Follow the repository's policy when one exists, including its allowed types,
scope rules, subject casing and length, required trailers, and merge or revert
exceptions. Honor its existing validator and hooks. Conventional Commits applies
only when repository documentation, configuration, or CI establishes it. When
no policy exists, write a concise descriptive message without installing a
validator or inventing a convention.

## Preserve partial staging

A commit without paths records the index. `git commit --only -- path` instead
records that path's current worktree contents: it does not mean “only the staged
hunks of this path.” Do not accidentally include a second, unstaged edit in the
same file. Inspect both diffs and choose the intended content before committing.

When unrelated content is already staged, preserve its staged blob and mode, not
just its worktree bytes. Use Git's index/stash facilities rather than manually
editing `.git/index` or temporarily discarding work. A scoped stash with later
index restoration or a separate `GIT_INDEX_FILE` can isolate the intended
snapshot; verify the actual tree and restore the original index state as
appropriate. Do not use an alternate index to evade commit hooks. Most clean
indexes need none of this machinery.

`git -C repo` does not change the parent shell's working directory. A relative
path printed by Git must not then be resolved against another repository. For
index isolation, `git -C repo rev-parse --path-format=absolute --git-path index`
identifies the intended worktree's index. Do not hard-code `.git/index`: linked
worktrees also have different administrative paths. See
[revision/path parsing](https://git-scm.com/docs/git-rev-parse), the
[commit contract](https://git-scm.com/docs/git-commit) and [Git
environment][source-1].

## Branches and release tags

A branch names a moving commit tip; a lightweight tag directly names an object,
while an annotated tag has its own message and identity. Follow the project's
release/signing policy. For a requested annotated tag, resolve the reviewed
commit and use `git tag -a TAG COMMIT -m MESSAGE`; use `-s` only when signing is
required and configured. Do not silently replace a signed tag with an unsigned
one when signing fails.

Inspect `git show TAG` and `git rev-parse TAG^{commit}` to verify the object and
peeled target. Creating a local tag does not publish it. Do not move an existing
release tag with `-f` to hide a wrong target; report the conflict and obtain the
intended repair. Version choice belongs to the release policy, not to Git's
lexicographic tag sorting. See the
[tag manual](https://git-scm.com/docs/git-tag).

Before any authorized remote update, confirm the remote and exact refspec.
Ordinary fetch, branch push, tag publication, and hosted release creation have
different effects. An authorized history replacement should bind
`--force-with-lease=refs/heads/BRANCH:EXPECTED_OID` to a reviewed remote value;
plain force discards concurrency protection. A lease does not authorize a push.
See [push](https://git-scm.com/docs/git-push).

[source-1]: https://git-scm.com/docs/git#Documentation/git.txt-GIT_INDEX_FILE
