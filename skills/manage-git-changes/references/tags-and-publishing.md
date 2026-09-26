# Tags and publishing

Local tags and the push operations that publish refs. Scenarios are in
[`assets/examples/verify.sh`](../assets/examples/verify.sh), including a
lease rejection against a local bare remote (git 2.55.0).

## Contents

- Annotated release tags
- Pushing a branch
- Force-with-lease
- Publishing tags

## Annotated release tags

**Definition.** `git tag -a NAME COMMIT -m MSG` creates a tag object with
its own message, tagger, and date; a lightweight tag is only a ref. `-s`
signs the tag when signing is configured ([git-tag][tag]).

**Use when.** Marking a release commit that the release policy names.

**Do not use when.** You would move an existing release tag with `-f` to
hide a wrong target; report the conflict instead. When signing is
required and fails, do not fall back to an unsigned tag.

**Example.**

```sh
git tag -a v1.4.0 "$REVIEWED_COMMIT" -m 'Release 1.4.0'
git show v1.4.0 --stat
git rev-parse 'v1.4.0^{commit}'
```

**Cost removed.** Tags on the wrong commit or without release metadata.

**Verify.**

1. `git cat-file -t v1.4.0` prints `tag`; `v1.4.0^{commit}` equals the
   reviewed commit (`verify.sh`).

## Pushing a branch

**Definition.** `git push REMOTE LOCAL:REMOTE_BRANCH` updates one remote
ref; `-u` records upstream tracking ([git-push][push]).

**Use when.** The user asked to publish a branch.

**Do not use when.** Nobody authorized it. A push publishes content that
may stay cached or mirrored after deletion.

**Example.**

```sh
git remote -v
git push -u origin feature/parser:feature/parser
```

**Cost removed.** Pushes to the wrong remote or branch.

**Verify.**

1. `git ls-remote origin refs/heads/feature/parser` shows the local
   commit.

## Force-with-lease

**Definition.** `git push --force-with-lease=REF:EXPECTED` overwrites the
remote ref only if it still points at `EXPECTED`; plain `--force`
overwrites whatever is there ([git-push][push]).

**Use when.** Publishing an authorized rewrite of a branch others may
also push to.

**Do not use when.** The lease value comes from a fetch whose changes you
did not review. A bare `--force-with-lease` compares against the
remote-tracking ref, which a background fetch can update.

**Example.**

```sh
expected=$(git rev-parse origin/feature)   # reviewed value
git push --force-with-lease="refs/heads/feature:$expected" \
  origin feature
```

**Cost removed.** Silently deleted collaborator commits. Measured: the
push was rejected after another clone pushed to the same branch.

**Verify.**

1. `verify.sh` pushes from a second clone, then asserts the leased push
   from the first clone fails.

## Publishing tags

**Definition.** A plain branch push does not push tags. Push a tag by name
(`git push origin v1.4.0`), or use `--follow-tags` for annotated tags
reachable from pushed commits.

**Use when.** The release process says to publish the tag.

**Do not use when.** You would run `git push --tags`, which publishes
every local tag, including experiments.

**Example.**

```sh
git push origin refs/tags/v1.4.0
```

**Cost removed.** Stray local tags published.

**Verify.**

1. `git ls-remote --tags origin v1.4.0` shows the tag object.

[tag]: https://git-scm.com/docs/git-tag
[push]: https://git-scm.com/docs/git-push
