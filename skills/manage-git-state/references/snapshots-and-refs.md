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

## Commit slices and snapshot evidence

Unless the user explicitly requests one commit, divide future commits by
independently understandable behavior rather than file count or diff size. Keep
an implementation with its relevant tests and necessary documentation. Run the
relevant checks for each commit so every slice is independently valid and can be
reverted without invalidating an unrelated slice. Apply this policy only to new
commits; do not rewrite existing history to reshape earlier work. A broad
authorization to commit current changes is not a single-commit override.

Choose boundaries from behavior and consumers, not filenames. Two independent
fixes in one file can need partial staging; one feature across source, tests and
docs can be one slice. For dependent work, put a valid prerequisite first and
record the dependency; revert dependents before their prerequisite. Keep changes
together when separating them would leave an invalid intermediate state.

For each slice, inspect the complete cached diff and run the checks that
distinguish its behavior. Checks against the dirty worktree can accidentally
depend on a later slice. When that risk exists, materialize the intended index
snapshot in disposable state and run the same repository checks there, with
required untracked fixtures supplied deliberately. Do not alter the user's
working files to simulate a clean snapshot.

Record `git write-tree` immediately before committing when exact snapshot
identity matters; compare it with `git rev-parse HEAD^{tree}` afterward. Inspect
the resulting full patch and message as well as status and remaining diffs.
A hook can succeed while changing the index: a different committed tree needs
review and checks, not an automatic success claim or unauthorized amendment.
After a failed hook, inspect HEAD, index and worktree before any retry. Preserve
unrelated staged blobs/modes, unstaged bytes and untracked files.
[Tree identity](https://git-scm.com/docs/git-write-tree).

## Commit messages

Before composing a message or running an operation that creates or rewords a
commit, determine the repository's configured message policy. Inspect its
contributor documentation, message-linter configuration, hook-manager
configuration, and equivalent CI gate. Use recent reachable history only as
supporting evidence, not as a substitute for an explicit policy. If these
sources conflict, stop and report the conflict instead of choosing a style.

Follow the repository's policy when one exists, including its allowed types,
scope rules, subject casing and length, required trailers, and merge or revert
exceptions. Honor its existing validator and hooks. When no policy exists, use
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):
`type(scope): summary`, with optional scope, `feat` for a feature, `fix` for a
bug fix, and other appropriate types for other work. Mark incompatible changes
with `!` or a `BREAKING CHANGE:` footer. This fallback is the skill's selected
policy, not a Git requirement. Do not install a validator or change repository
policy as part of composing a message.

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
